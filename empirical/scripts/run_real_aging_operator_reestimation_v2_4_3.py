from __future__ import annotations
from pathlib import Path
import sys, json, re, csv
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from acmf.aging_transition_matrix import fixed_alpha, transition_matrix
from empirical.scripts.pipeline import (
    RAW, OUT, REP, sha256, rows, num,
    parse_population, parse_deaths, parse_international, parse_interprov_in, parse_growth, parse_births,
    aggregate_pop, predict, baselines, metrics, stage_trace
)

AGE_BINS = {
    '0 to 4 years': list(range(0, 5)),
    '5 to 9 years': list(range(5, 10)),
    '10 to 14 years': list(range(10, 15)),
    '15 to 19 years': list(range(15, 20)),
    '20 to 24 years': list(range(20, 25)),
    '25 to 29 years': list(range(25, 30)),
    '30 to 34 years': list(range(30, 35)),
    '35 to 39 years': list(range(35, 40)),
    '40 to 44 years': list(range(40, 45)),
    '45 to 49 years': list(range(45, 50)),
    '50 to 54 years': list(range(50, 55)),
    '55 to 59 years': list(range(55, 60)),
    '60 to 64 years': list(range(60, 65)),
    '65 to 69 years': list(range(65, 70)),
    '70 to 74 years': list(range(70, 75)),
    '75 to 79 years': list(range(75, 80)),
    '80 to 84 years': list(range(80, 85)),
    '85 to 89 years': list(range(85, 90)),
    '90 to 94 years': list(range(90, 95)),
    '95 to 99 years': list(range(95, 100)),
}

def parse_single_age_2021() -> pd.DataFrame:
    p = RAW / '9810002301-eng.csv'
    if not p.exists():
        return pd.DataFrame()
    data = rows(p)
    geo_row = next(i for i, r in enumerate(data) if r and r[0] == 'Geography')
    gender_row = geo_row + 1
    geos = []
    last = ''
    for x in data[geo_row][1:]:
        if x:
            last = re.sub(r'\s+i\d+$', '', str(x)).strip()
        geos.append(last)
    genders_raw = data[gender_row][1:]
    genders = []
    last_g = ''
    for g in genders_raw:
        if g:
            last_g = re.sub(r'\s+\d+(\s+\d+)*$', '', g).strip()
        genders.append(last_g)
    rec = []
    for r in data[geo_row + 3:]:
        if not r or r[0].startswith('Average age') or r[0].startswith('Abbreviation notes'):
            break
        label = r[0].strip()
        if label == 'Under 1 year':
            age = 0
        elif re.fullmatch(r'\d+', label.strip()):
            age = int(label.strip())
        elif label == '100 years and over':
            age = 100
        else:
            continue
        for j, val in enumerate(r[1:]):
            if j < len(geos) and geos[j] and j < len(genders) and genders[j] in {'Men+', 'Women+'}:
                rec.append({'geo': geos[j], 'gender': genders[j], 'age_single': age, 'year': 2021, 'population': num(val)})
    df = pd.DataFrame(rec).dropna(subset=['population'])
    return df

def estimate_alpha_from_single_age(single: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    alpha = fixed_alpha(0.2)
    rows_out = []
    for group, ages in AGE_BINS.items():
        total = single[single.age_single.isin(ages)].population.sum()
        exit_pop = single[single.age_single.eq(max(ages))].population.sum()
        frac = float(exit_pop / total) if total > 0 else 0.2
        # Bound it but do not normalize it to 0.2.
        frac = float(min(max(frac, 0.0), 0.95))
        alpha[group] = frac
        rows_out.append({'age_group': group, 'source': '9810002301_single_age_2021', 'last_single_age': max(ages), 'bin_population': float(total), 'last_age_population': float(exit_pop), 'outflow_fraction': frac})
    alpha['-1 year'] = 0.0
    alpha['100 years and older'] = 0.0
    rows_out.append({'age_group': '-1 year', 'source': 'fixed_non_state', 'last_single_age': None, 'bin_population': None, 'last_age_population': None, 'outflow_fraction': 0.0})
    rows_out.append({'age_group': '100 years and older', 'source': 'open_interval_retained', 'last_single_age': 100, 'bin_population': float(single[single.age_single.ge(100)].population.sum()), 'last_age_population': float(single[single.age_single.ge(100)].population.sum()), 'outflow_fraction': 0.0})
    return alpha, pd.DataFrame(rows_out)

def dense_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index='age_from', columns='age_to', values='probability', aggfunc='sum').fillna(0.0)

def matrix_diff(alpha_emp: dict, alpha_fixed: dict) -> dict:
    te = transition_matrix(alpha_emp)
    tf = transition_matrix(alpha_fixed)
    de = dense_matrix(te)
    df = dense_matrix(tf)
    all_idx = sorted(set(de.index) | set(df.index))
    all_cols = sorted(set(de.columns) | set(df.columns))
    A = de.reindex(index=all_idx, columns=all_cols, fill_value=0.0).values
    B = df.reindex(index=all_idx, columns=all_cols, fill_value=0.0).values
    D = A - B
    return {'max_abs_diff': float(np.max(np.abs(D))), 'frobenius_norm': float(np.sqrt(np.sum(D * D))), 'nonzero_entries': int(np.sum(np.abs(D) > 1e-12))}

def target_diff(a: pd.DataFrame, b: pd.DataFrame, name_a: str, name_b: str) -> pd.DataFrame:
    m = a.merge(b, on=['geo', 'year'], suffixes=(f'_{name_a}', f'_{name_b}'))
    out = []
    for t in ['P1_0_14', 'P2_15_64', 'P3_65plus', 'P_tot']:
        d = m[f'{t}_{name_a}'] - m[f'{t}_{name_b}']
        out.append({'target': t, 'max_abs_diff': float(np.abs(d).max()), 'mean_abs_diff': float(np.abs(d).mean()), 'allclose': bool(np.allclose(m[f'{t}_{name_a}'], m[f'{t}_{name_b}']))})
    return pd.DataFrame(out)

def aggregate_stage(stage_df: pd.DataFrame) -> pd.DataFrame:
    P1 = {'-1 year','0 to 4 years','5 to 9 years','10 to 14 years'}
    P2 = {'15 to 19 years','20 to 24 years','25 to 29 years','30 to 34 years','35 to 39 years','40 to 44 years','45 to 49 years','50 to 54 years','55 to 59 years','60 to 64 years'}
    P3 = {'65 to 69 years','70 to 74 years','75 to 79 years','80 to 84 years','85 to 89 years','90 to 94 years','95 to 99 years','100 years and older'}
    tmp = stage_df.rename(columns={'population_pred': 'population'}).copy()
    tmp['cohort'] = tmp.age_group.map(lambda a: 'P1_0_14' if a in P1 else ('P2_15_64' if a in P2 else ('P3_65plus' if a in P3 else None)))
    tmp = tmp.dropna(subset=['cohort'])
    out = tmp.groupby(['operator', 'stage', 'geo', 'year', 'cohort'], as_index=False).population.sum().pivot_table(index=['operator','stage','geo','year'], columns='cohort', values='population', aggfunc='sum').reset_index()
    out.columns.name = None
    for c in ['P1_0_14','P2_15_64','P3_65plus']:
        if c not in out:
            out[c] = 0.0
    out['P_tot'] = out[['P1_0_14','P2_15_64','P3_65plus']].sum(axis=1)
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True); REP.mkdir(parents=True, exist_ok=True)
    input_hashes = {p.name: sha256(p) for p in sorted(RAW.glob('*.csv'))}
    pop = parse_population(); deaths = parse_deaths(); intl = parse_international(); inp = parse_interprov_in(); growth = parse_growth(); births = parse_births(); obs = aggregate_pop(pop)
    single = parse_single_age_2021()
    single.to_csv(OUT / 'v2_4_3_single_age_2021_clean.csv', index=False)
    alpha_real, alpha_source = estimate_alpha_from_single_age(single)
    alpha_fixed = fixed_alpha(0.2)
    alpha_source['fixed20_outflow'] = alpha_source['age_group'].map(alpha_fixed)
    alpha_source['diff_vs_fixed20'] = alpha_source['outflow_fraction'] - alpha_source['fixed20_outflow']
    alpha_source.to_csv(OUT / 'v2_4_3_real_aging_outflow_fractions.csv', index=False)
    transition_matrix(alpha_real).to_csv(OUT / 'v2_4_3_real_aging_transition_matrix.csv', index=False)
    transition_matrix(alpha_fixed).to_csv(OUT / 'v2_4_3_fixed20_transition_matrix.csv', index=False)
    mdiff = matrix_diff(alpha_real, alpha_fixed)
    # Predictions and stage traces
    years = [2022, 2023, 2024]
    pred_fixed_age = predict(pop, alpha_fixed, years, deaths, intl, inp, growth, births)
    pred_real_age = predict(pop, alpha_real, years, deaths, intl, inp, growth, births)
    p_fixed = aggregate_pop(pred_fixed_age.rename(columns={'population_pred':'population'})); p_real = aggregate_pop(pred_real_age.rename(columns={'population_pred':'population'}))
    p_fixed.to_csv(OUT / 'v2_4_3_predictions_fixed20_p123.csv', index=False)
    p_real.to_csv(OUT / 'v2_4_3_predictions_real_aging_p123.csv', index=False)
    pdiff = target_diff(p_real, p_fixed, 'real', 'fixed20')
    pdiff.to_csv(OUT / 'v2_4_3_prediction_diff_real_vs_fixed20.csv', index=False)
    traces = []
    for year in [2022, 2023, 2024]:
        pt = pop[pop.year.eq(year)]
        f = stage_trace(pt, alpha_fixed, year, deaths, intl, inp, growth, births); f['operator'] = 'fixed20'; traces.append(f)
        r = stage_trace(pt, alpha_real, year, deaths, intl, inp, growth, births); r['operator'] = 'real_single_age'; traces.append(r)
    trace = pd.concat(traces, ignore_index=True)
    trace.to_csv(OUT / 'v2_4_3_stage_trace_age_gender.csv', index=False)
    ag = aggregate_stage(trace)
    ag.to_csv(OUT / 'v2_4_3_stage_trace_p123.csv', index=False)
    stage_diffs = []
    for stage in sorted(ag.stage.unique()):
        f = ag[(ag.operator.eq('fixed20')) & (ag.stage.eq(stage))]
        r = ag[(ag.operator.eq('real_single_age')) & (ag.stage.eq(stage))]
        d = target_diff(r, f, 'real', 'fixed20'); d['stage'] = stage; stage_diffs.append(d)
    stage_diff = pd.concat(stage_diffs, ignore_index=True)
    stage_diff.to_csv(OUT / 'v2_4_3_stage_prediction_diff.csv', index=False)
    # Component ablation for real operator only compared to fixed20 all components and baselines
    component_sets = [('aging_only',()),('aging_births',('births',)),('aging_births_deaths',('births','deaths')),('aging_births_deaths_international',('births','deaths','international')),('aging_births_deaths_international_interprovincial',('births','deaths','international','interprovincial'))]
    obs_eval = obs[obs.year.isin([2023,2024,2025])]
    all_metrics = []
    for label, comps in component_sets:
        pr = predict(pop, alpha_real, years, deaths, intl, inp, growth, births, components=comps)
        pp = aggregate_pop(pr.rename(columns={'population_pred':'population'})); pp['model'] = f'real_single_age_{label}'
        all_metrics += metrics(pp, obs_eval, f'real_single_age_{label}')
    all_metrics += metrics(p_fixed, obs_eval, 'fixed20_all_components')
    base = baselines(obs)
    for model, grp in base.groupby('model'):
        all_metrics += metrics(grp, obs_eval, model)
    met = pd.DataFrame(all_metrics)
    met.to_csv(OUT / 'v2_4_3_component_ablation_metrics.csv', index=False)
    summary = met[met.geo.eq('ALL')]
    best = summary.sort_values(['target','rmse']).groupby('target').first().reset_index()[['target','model','rmse','mae','relative_rmse','n']]
    # Deltas in real component chain
    deltas = []
    chain = [f'real_single_age_{x[0]}' for x in component_sets]
    for target in ['P1_0_14','P2_15_64','P3_65plus','P_tot']:
        vals = [float(summary[(summary.model.eq(m)) & (summary.target.eq(target))].rmse.iloc[0]) for m in chain]
        for i in range(1, len(vals)):
            deltas.append({'target': target, 'from_model': chain[i-1], 'to_model': chain[i], 'delta_rmse': vals[i]-vals[i-1], 'rmse_before': vals[i-1], 'rmse_after': vals[i]})
    pd.DataFrame(deltas).to_csv(OUT / 'v2_4_3_component_delta_rmse.csv', index=False)
    # Tests / conclusions
    matrix_diff_ok = mdiff['max_abs_diff'] > 0 and mdiff['frobenius_norm'] > 0
    output_diff_ok = float(pdiff.max_abs_diff.max()) > 0
    after_aging_diff = stage_diff[stage_diff.stage.eq('after_aging')].max_abs_diff.max()
    stage_diff_ok = float(after_aging_diff) > 0
    report = {
        'status': 'PASS_WITH_FINDINGS' if matrix_diff_ok and output_diff_ok and stage_diff_ok else 'FAIL_REESTIMATION_NOT_EFFECTIVE',
        'input_hashes': input_hashes,
        'transition_matrix_diff_vs_fixed20': mdiff,
        'matrix_diff_ok': matrix_diff_ok,
        'output_diff_ok': output_diff_ok,
        'stage_after_aging_diff_ok': stage_diff_ok,
        'prediction_diff_summary': pdiff.to_dict('records'),
        'stage_diff_summary': stage_diff.to_dict('records'),
        'best_by_target': best.to_dict('records'),
        'interpretation': {
            'what_was_tested': 'v2.4.3 estimates aging outflow fractions from the 2021 single-age census distribution and explicitly tests T_real != T_fixed and predictions_real != predictions_fixed.',
            'caveat': 'The single-age census is a cross-sectional anchor, not a longitudinal transition series; this is a stronger pipeline test and practical re-estimation, not a final demographic law.',
        },
        'known_limitations': [
            'Observed demographic components are still used in accounting-mode predictions.',
            'Single-age distribution is a 2021 cross-sectional census anchor.',
            'No uncertainty propagation yet.',
            'Interprovincial net migration by age/gender is approximated.',
        ]
    }
    (REP / 'v2_4_3_real_aging_reestimation_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['# v2.4.3 Real Aging Operator Re-estimation Audit', '', f"Status: **{report['status']}**", '', '## Matrix-level test', f"- `max_abs_diff(T_real, T_fixed20)`: {mdiff['max_abs_diff']}", f"- `frobenius_norm(T_real - T_fixed20)`: {mdiff['frobenius_norm']}", f"- `nonzero_entries`: {mdiff['nonzero_entries']}", '', '## Output-level test']
    for r in report['prediction_diff_summary']:
        lines.append(f"- `{r['target']}`: max_abs_diff={r['max_abs_diff']}, mean_abs_diff={r['mean_abs_diff']}, allclose={r['allclose']}")
    lines += ['', '## Stage after-aging test']
    for r in [x for x in report['stage_diff_summary'] if x['stage']=='after_aging']:
        lines.append(f"- `{r['target']}`: max_abs_diff={r['max_abs_diff']}, allclose={r['allclose']}")
    lines += ['', '## Best by target']
    for r in report['best_by_target']:
        lines.append(f"- `{r['target']}`: `{r['model']}` RMSE={r['rmse']:.2f}, relative_RMSE={r['relative_rmse']:.6f}")
    lines += ['', '## Interpretation', report['interpretation']['what_was_tested'], '', report['interpretation']['caveat'], '', '## Known limitations'] + [f"- {x}" for x in report['known_limitations']]
    (REP / 'v2_4_3_real_aging_reestimation_report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'matrix_diff': mdiff, 'output_diff_ok': output_diff_ok, 'best_by_target': report['best_by_target']}, indent=2))

if __name__ == '__main__':
    main()

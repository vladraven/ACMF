from pathlib import Path
import json,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    failures=[]
    req=['empirical/reports/v2_4_2_trace_audit_report.json','empirical/processed/v2_4_2_full_stage_trace_age_gender.csv','empirical/processed/v2_4_2_stage_prediction_diff.csv','empirical/processed/v2_4_2_component_delta_rmse.csv','empirical/processed/v2_4_2_p_tot_forecast_vs_accounting.csv']
    for rel in req:
        if not (ROOT/rel).exists(): failures.append(f'missing {rel}')
    if not failures:
        rep=json.loads((ROOT/'empirical/reports/v2_4_2_trace_audit_report.json').read_text())
        if rep.get('status')!='PASS_WITH_FINDINGS': failures.append('unexpected report status')
        tr=pd.read_csv(ROOT/'empirical/processed/v2_4_2_full_stage_trace_age_gender.csv')
        if len(tr)==0: failures.append('empty trace')
        sd=pd.read_csv(ROOT/'empirical/processed/v2_4_2_stage_prediction_diff.csv')
        if not {'stage','target','max_abs_diff','allclose'}.issubset(sd.columns): failures.append('bad stage diff schema')
    result={'status':'PASS' if not failures else 'FAIL','failures':failures}
    (ROOT/'empirical/reports/v2_4_2_test_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if failures: raise SystemExit(1)
if __name__=='__main__': main()

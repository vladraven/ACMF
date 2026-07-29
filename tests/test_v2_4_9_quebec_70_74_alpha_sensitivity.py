from pathlib import Path
import json,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    failures=[]
    req=['empirical/reports/v2_4_9_quebec_70_74_alpha_sensitivity_report.json','empirical/processed/v2_4_9_quebec_70_74_alpha_grid.csv','empirical/processed/v2_4_9_quebec_70_74_alpha_models_summary.csv','empirical/processed/v2_4_9_quebec_70_74_yearly_predictions_by_model.csv','empirical/processed/v2_4_9_quebec_70_74_gender_component_trace_by_model.csv']
    for rel in req:
        if not (ROOT/rel).exists(): failures.append(f'missing {rel}')
    if not failures:
        rep=json.loads((ROOT/'empirical/reports/v2_4_9_quebec_70_74_alpha_sensitivity_report.json').read_text())
        if rep.get('status')!='PASS_WITH_FINDINGS': failures.append('bad status')
        grid=pd.read_csv(ROOT/'empirical/processed/v2_4_9_quebec_70_74_alpha_grid.csv')
        if len(grid)<100: failures.append('grid too small')
        summ=pd.read_csv(ROOT/'empirical/processed/v2_4_9_quebec_70_74_alpha_models_summary.csv')
        if not {'real_single_age','fixed20','best_grid_rmse','best_grid_mae'}.issubset(set(summ.model)): failures.append('missing model candidates')
    result={'status':'PASS' if not failures else 'FAIL','failures':failures}; (ROOT/'empirical/reports/v2_4_9_test_report.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
    if failures: raise SystemExit(1)
if __name__=='__main__': main()

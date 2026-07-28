from pathlib import Path
import json
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
def main():
    failures=[]
    required = [
        'empirical/reports/v2_4_3_real_aging_reestimation_report.json',
        'empirical/processed/v2_4_3_real_aging_transition_matrix.csv',
        'empirical/processed/v2_4_3_fixed20_transition_matrix.csv',
        'empirical/processed/v2_4_3_prediction_diff_real_vs_fixed20.csv',
        'empirical/processed/v2_4_3_stage_prediction_diff.csv',
        'empirical/processed/v2_4_3_component_ablation_metrics.csv',
    ]
    for rel in required:
        if not (ROOT/rel).exists(): failures.append(f'missing {rel}')
    if not failures:
        rep=json.loads((ROOT/'empirical/reports/v2_4_3_real_aging_reestimation_report.json').read_text())
        if rep.get('status')!='PASS_WITH_FINDINGS': failures.append('report status is not PASS_WITH_FINDINGS')
        if not rep.get('matrix_diff_ok'): failures.append('matrix diff test failed')
        if not rep.get('output_diff_ok'): failures.append('output diff test failed')
        if not rep.get('stage_after_aging_diff_ok'): failures.append('after-aging stage diff test failed')
        diff=pd.read_csv(ROOT/'empirical/processed/v2_4_3_prediction_diff_real_vs_fixed20.csv')
        if float(diff.max_abs_diff.max()) <= 0: failures.append('prediction max diff is zero')
    result={'status':'PASS' if not failures else 'FAIL','failures':failures}
    (ROOT/'empirical/reports/v2_4_3_test_report.json').write_text(json.dumps(result,indent=2), encoding='utf-8')
    print(json.dumps(result,indent=2))
    if failures: raise SystemExit(1)
if __name__=='__main__': main()

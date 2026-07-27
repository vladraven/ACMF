from pathlib import Path
import json, pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    failures=[]
    for rel in ["acmf_core.py","params.py","acmf_solver.py","acmf/demography_age_structured.py","empirical/scripts/build_full_package.py"]:
        if not (ROOT/rel).exists(): failures.append(f"missing {rel}")
    r=ROOT/"empirical/reports/v2_1_build_report.json"
    if not r.exists(): failures.append("missing build report")
    else:
        rep=json.loads(r.read_text())
        for k,v in rep.get("test_results",{}).items():
            if v not in {"PASS","SKIP_NO_FILE"}: failures.append(f"{k}={v}")
    out=ROOT/"empirical/processed/economic_region_components_2024_2025_long.csv"
    if out.exists():
        df=pd.read_csv(out)
        if len(df)==0: failures.append("parsed economic region output empty")
    result={"status":"PASS" if not failures else "FAIL","failures":failures}
    (ROOT/"empirical/reports/v2_1_package_test_report.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    if failures: raise SystemExit(1)
if __name__=="__main__": main()

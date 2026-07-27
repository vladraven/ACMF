from pathlib import Path
import json, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from params import get_default_params
from acmf_core import rhs_acmf
from acmf_solver import solve_acmf
from acmf.demography_age_structured import aggregate_to_p123
import pandas as pd

def main():
    failures=[]
    p=get_default_params(2); D=np.array([[0,1],[1,0]],float); y0=np.ones((2,12))*0.5; y0[:,9:12]=[1000,5000,1000]
    try:
        dy=rhs_acmf(0,y0.ravel(),p,D)
        if dy.shape != (24,): failures.append("rhs shape incorrect")
        sol=solve_acmf(y0,(0,1),p,D,max_step=1)
        if not sol.success: failures.append("solver failed")
    except Exception as e: failures.append(f"core exception: {e}")
    try:
        df=pd.DataFrame({"geo":["X","X","X"],"year":[2025]*3,"gender":["Men+"]*3,"age_group":["0 to 4 years","15 to 19 years","65 to 69 years"],"population":[10,20,30]})
        out=aggregate_to_p123(df)
        if float(out.P1.iloc[0])!=10 or float(out.P2.iloc[0])!=20 or float(out.P3.iloc[0])!=30: failures.append("aggregate_to_p123 wrong")
    except Exception as e: failures.append(f"demography exception: {e}")
    result={"status":"PASS" if not failures else "FAIL","failures":failures}
    (ROOT/"empirical/reports/core_test_report.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    if failures: raise SystemExit(1)
if __name__=="__main__": main()

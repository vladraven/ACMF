from __future__ import annotations
import numpy as np
import pandas as pd

def rmse(y, yhat):
    y=np.asarray(y,float); yhat=np.asarray(yhat,float); m=np.isfinite(y)&np.isfinite(yhat)
    return float(np.sqrt(np.mean((y[m]-yhat[m])**2))) if m.any() else float('nan')
def mae(y, yhat):
    y=np.asarray(y,float); yhat=np.asarray(yhat,float); m=np.isfinite(y)&np.isfinite(yhat)
    return float(np.mean(np.abs(y[m]-yhat[m]))) if m.any() else float('nan')
def mape(y, yhat, eps=1e-9):
    y=np.asarray(y,float); yhat=np.asarray(yhat,float); m=np.isfinite(y)&np.isfinite(yhat)&(np.abs(y)>eps)
    return float(np.mean(np.abs((y[m]-yhat[m])/y[m]))*100) if m.any() else float('nan')
def r2_score(y, yhat):
    y=np.asarray(y,float); yhat=np.asarray(yhat,float); m=np.isfinite(y)&np.isfinite(yhat)
    if m.sum()<2: return float('nan')
    ssr=float(np.sum((y[m]-yhat[m])**2)); sst=float(np.sum((y[m]-np.mean(y[m]))**2))
    return float(1.0-ssr/sst) if sst>0 else float('nan')
def metrics_for_series(y, yhat):
    return {'RMSE':rmse(y,yhat),'MAE':mae(y,yhat),'MAPE':mape(y,yhat),'R2':r2_score(y,yhat)}
def metrics_dataframe(observed: dict, predicted: dict, variables: list[str]) -> pd.DataFrame:
    rows=[]
    for v in variables:
        d=metrics_for_series(observed[v], predicted[v]); d['variable']=v; rows.append(d)
    return pd.DataFrame(rows)[['variable','RMSE','MAE','MAPE','R2']]

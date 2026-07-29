"""Minimal FastAPI wrapper for ACMF tasks.

Security: POST /run/{task} requires a bearer token when ACMF_API_TOKEN is set.
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'src'
TASKS={'health','v2_4_9','empirical_canada','synthetic_ladder','world_profile','world_ident','data_list_indicators','data_fisher_rank','data_build_minimal','data_build_standard','datacube_init','datacube_build'}
app=FastAPI(title='ACMF Runner')

def _authorize(authorization: str | None):
    token=os.getenv('ACMF_API_TOKEN')
    if not token:
        return
    if authorization != f'Bearer {token}':
        raise HTTPException(status_code=401, detail='missing or invalid bearer token')

@app.get('/health')
def health():
    return {'status':'ok'}

@app.post('/run/{task}')
def run_task(task: str, authorization: str | None = Header(default=None)):
    _authorize(authorization)
    if task not in TASKS:
        raise HTTPException(status_code=404, detail=f'unknown task: {task}')
    env=os.environ.copy(); env['PYTHONPATH']=str(SRC)+os.pathsep+env.get('PYTHONPATH','')
    proc=subprocess.run([sys.executable,'main.py','--task',task],cwd=ROOT,env=env,text=True,capture_output=True,timeout=900)
    return {'task':task,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}

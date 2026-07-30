from __future__ import annotations
from flask import Flask, jsonify, request
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from acmf.task_runner import available_tasks, run_task_captured
app=Flask(__name__)

@app.get('/')
def index():
    return jsonify({'app':'ACMF','version':'3.3.1.9-clean-quality-hardening','tasks':available_tasks()})

@app.post('/run/<task>')
def run(task):
    token=os.environ.get('ACMF_API_TOKEN')
    if token and request.headers.get('Authorization') != f'Bearer {token}':
        return jsonify({'error':'unauthorized'}),401
    if task not in available_tasks():
        return jsonify({'error':'unknown task','available_tasks':available_tasks()}),400
    return jsonify(run_task_captured(task))

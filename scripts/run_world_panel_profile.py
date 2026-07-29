#!/usr/bin/env python3
from __future__ import annotations
import sys, json, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.world_panel import load_world_panel, world_panel_profile, top_countries_by_coverage

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',default=None); ap.add_argument('--output',default='output/world_panel_profile.json'); ap.add_argument('--top-n',type=int,default=10); a=ap.parse_args()
    df=load_world_panel(a.data); profile=world_panel_profile(df); profile['top_countries']=top_countries_by_coverage(df,n=a.top_n); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(profile,indent=2),encoding='utf-8')
    print(json.dumps({'rows':profile['rows'],'countries_count':profile['countries_count'],'year_min':profile['year_min'],'year_max':profile['year_max'],'indicator_count':profile['indicator_count'],'top_countries':profile['top_countries'],'lowest_indicator_coverage':sorted(profile['indicator_coverage'], key=lambda x:x['coverage_pct'])[:5]},indent=2)); print(f'saved: {out}')
if __name__=='__main__': main()

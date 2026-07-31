#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acmf.empirical_validation import run_country_validation, run_core5_validation, write_validation_outputs, indicator_ablation_study, backtest_2008, CORE5, _safe
from acmf.model_levels import available_model_levels

def main():
    p=argparse.ArgumentParser(description='Run ACMF empirical validation')
    p.add_argument('--mode', choices=['country','core5','ablation','backtest-2008'], default='core5')
    p.add_argument('--country', default='Canada')
    p.add_argument('--countries', nargs='*', default=CORE5)
    p.add_argument('--train-start', type=int, default=1995)
    p.add_argument('--train-end', type=int, default=2015)
    p.add_argument('--validation-start', type=int, default=2016)
    p.add_argument('--validation-end', type=int, default=2024)
    p.add_argument('--seeds', nargs='*', type=int, default=[0,1,2])
    p.add_argument('--max-nfev', type=int, default=60)
    p.add_argument('--model-level', default='R5', choices=available_model_levels())
    p.add_argument('--output-dir', default='output/empirical_validation')
    args=p.parse_args()
    if args.mode=='country':
        r=run_country_validation(args.country,args.train_start,args.train_end,args.validation_start,args.validation_end,seeds=args.seeds,max_nfev=args.max_nfev, model_level=args.model_level)
        report={'country_reports':[r],'runs':r['runs'],'metrics':r['best_metrics'],'yearly_errors':r['yearly_errors']}
        from acmf.empirical_validation import parameter_stability_report, identifiability_map
        report['parameter_stability']=parameter_stability_report(report['runs']); report['identifiability_map']=identifiability_map(report['runs'])
        out=write_validation_outputs(report,args.output_dir)
        print(json.dumps(_safe({'output_dir':str(out),'country':args.country,'model_level':args.model_level,'mean_RMSE':float(report['metrics']['RMSE'].mean())}), indent=2))
    elif args.mode=='core5':
        r=run_core5_validation(args.countries, train_start=args.train_start, train_end=args.train_end, validation_start=args.validation_start, validation_end=args.validation_end, seeds=args.seeds, max_nfev=args.max_nfev, model_level=args.model_level)
        out=write_validation_outputs(r,args.output_dir)
        print(json.dumps(_safe({'output_dir':str(out),'countries':args.countries,'model_level':args.model_level,'mean_RMSE':float(r['metrics']['RMSE'].mean()),'identifiability_map':r['identifiability_map'].to_dict(orient='records')}), indent=2))
    elif args.mode=='ablation':
        df=indicator_ablation_study(country=args.country, train_start=args.train_start, train_end=args.train_end, validation_start=args.validation_start, validation_end=args.validation_end, seed=args.seeds[0], model_level=args.model_level)
        out=Path(args.output_dir); out.mkdir(parents=True, exist_ok=True); df.to_csv(out/'ablation_results.csv', index=False)
        print(json.dumps(_safe({'output':str(out/'ablation_results.csv'),'country':args.country,'model_level':args.model_level,'rows':len(df)}), indent=2))
    else:
        r=backtest_2008(args.country, seed=args.seeds[0], model_level=args.model_level); out=Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
        r['best_metrics'].to_csv(out/'backtest_2008_summary.csv', index=False)
        print(json.dumps(_safe({'output':str(out/'backtest_2008_summary.csv'),'country':args.country,'model_level':args.model_level,'mean_RMSE':float(r['best_metrics']['RMSE'].mean())}), indent=2))
if __name__=='__main__':
    main()

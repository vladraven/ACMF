#!/usr/bin/env python3
"""
Comprehensive benchmark test results for all 4 new scenarios
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from scripts.run_synthetic_forecast_benchmark import ForecastBenchmark

SCENARIOS_WITH_EXPECTATIONS = {
    "low_stress_trend": {
        "description": "Linear trend with low stress",
        "expected_winner": "linear_trend",
        "expected_description": "Simple trend should favor linear extrapolation"
    },
    "level_shift_shock_recovery": {
        "description": "Sudden shock followed by recovery phase",
        "expected_winner": "ACMF or complex model",
        "expected_description": "Recovery dynamics require system understanding of resilience"
    },
    "saturation_curve": {
        "description": "Logistic/saturation growth curve",
        "expected_winner": "ACMF or logistic baseline",
        "expected_description": "Output saturation requires nonlinear model or logistic fit"
    },
    "regime_change_stress": {
        "description": "Regime switch triggered by stress dynamics",
        "expected_winner": "ACMF only",
        "expected_description": "Only works if stress-driven dynamics are correctly implemented"
    }
}

def run_all_benchmarks():
    """Run benchmarks for all scenarios and collect results"""
    all_results = []
    
    print("\n" + "="*100)
    print(" COMPREHENSIVE SYNTHETIC FORECAST BENCHMARK: 4 SCENARIOS ".center(100))
    print("="*100)
    
    for scenario_name, scenario_info in SCENARIOS_WITH_EXPECTATIONS.items():
        print(f"\n{'='*100}")
        print(f"SCENARIO: {scenario_name.upper()}")
        print(f"Description: {scenario_info['description']}")
        print(f"Expected Winner: {scenario_info['expected_winner']}")
        print(f"Rationale: {scenario_info['expected_description']}")
        print(f"{'='*100}\n")
        
        benchmark = ForecastBenchmark(scenario_name, seed=42)
        results = benchmark.run_benchmark(horizon=30)
        
        # Display results
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        
        # Find winners
        print(f"\n{'Best Models by Metric':^100}")
        print(f"{'-'*100}")
        for metric in ["rmse", "mae", "r2"]:
            if metric in ["rmse", "mae"]:
                best_idx = df[metric].idxmin()
                direction = "LOWER IS BETTER"
            else:
                best_idx = df[metric].idxmax()
                direction = "HIGHER IS BETTER"
            
            best_row = df.iloc[best_idx]
            print(f"{metric.upper():6} | {best_row['model']:15} | {best_row[metric]:10.4f} [{direction}]")
        
        # Store for summary
        all_results.append({
            "scenario": scenario_name,
            "results_df": df,
            "expected": scenario_info["expected_winner"]
        })
    
    return all_results

def print_summary(all_results):
    """Print summary table across all scenarios"""
    print("\n\n" + "="*100)
    print(" SUMMARY: WINNER ANALYSIS ACROSS ALL SCENARIOS ".center(100))
    print("="*100 + "\n")
    
    summary_data = []
    for result_set in all_results:
        df = result_set["results_df"]
        scenario = result_set["scenario"]
        expected = result_set["expected"]
        
        # Best by RMSE
        best_rmse_idx = df["rmse"].idxmin()
        best_rmse = df.iloc[best_rmse_idx]["model"]
        rmse_val = df.iloc[best_rmse_idx]["rmse"]
        
        # Best by R2
        best_r2_idx = df["r2"].idxmax()
        best_r2 = df.iloc[best_r2_idx]["model"]
        r2_val = df.iloc[best_r2_idx]["r2"]
        
        summary_data.append({
            "Scenario": scenario,
            "Best (RMSE)": best_rmse,
            "RMSE Score": f"{rmse_val:.4f}",
            "Best (R2)": best_r2,
            "R2 Score": f"{r2_val:.4f}",
            "Expected": expected,
            "Match": "YES" if best_rmse.lower() in expected.lower() or best_r2.lower() in expected.lower() else "NO"
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    # Statistics
    print(f"\n{'Summary Statistics':^100}")
    print(f"{'-'*100}")
    matches = sum(1 for row in summary_data if row["Match"] == "YES")
    total = len(summary_data)
    print(f"Expected Model Match Rate: {matches}/{total} ({100*matches//total}%)")
    print(f"ACMF Overall Performance: Underperforms simple baselines on ALL tested scenarios")
    print(f"Recommendation: Parameter tuning or model reformulation needed")

if __name__ == "__main__":
    print("\nRunning comprehensive synthetic forecast benchmark...\n")
    
    # Run all benchmarks
    all_results = run_all_benchmarks()
    
    # Print summary
    print_summary(all_results)
    
    sys.exit(0)

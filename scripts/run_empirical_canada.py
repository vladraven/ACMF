import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pathlib import Path
from acmf.empirical import run_empirical_csv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "canada_fred_population_fertility_empirical.csv"

result = run_empirical_csv(DATA)
print("Decision:")
print(result["decision"])
print("\nMetrics:")
print(result["metrics"].to_string(index=False))


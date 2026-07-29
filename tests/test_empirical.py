from pathlib import Path
from acmf.empirical import load_research_csv


def test_canada_dataset_loads():
    path = Path(__file__).resolve().parents[1] / "data" / "canada_fred_population_fertility_empirical.csv"
    df = load_research_csv(path)
    assert len(df) >= 40
    assert {"t", "dy", "x"}.issubset(df.columns)

from __future__ import annotations
AGE_BINS = {'0_14': range(0,15), '15_64': range(15,65), '65_plus': range(65,121)}

def cohort_label(age: int) -> str:
    if age < 0:
        raise ValueError('age must be non-negative')
    for label, ages in AGE_BINS.items():
        if age in ages:
            return label
    raise ValueError(f'age {age} outside supported range 0-120')

def aggregate_age_counts(age_counts: dict[int, float]) -> dict[str, float]:
    out={label:0.0 for label in AGE_BINS}
    for age, count in age_counts.items():
        out[cohort_label(int(age))] += float(count)
    return out

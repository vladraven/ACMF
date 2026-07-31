# ACMF 4.2.0 — Institutional Loop Repair and Sensitivity
**Дата:** 2026-07-31  
**Коммит:** `3c21c62`  
**Ветка:** `main`

---

## Цель релиза

Понять, почему `inst_drag > inst_pull` во всех диагностических сценариях, и идентифицировать структурную причину без искусственной подгонки RMSE.

---

## Что деплоилось

### Новые файлы

| Файл | Описание |
|------|----------|
| `scripts/run_institutional_loop_diagnostics.py` | Трассировка pull/drag по компонентам на каждом шаге симуляции |
| `scripts/run_institutional_sensitivity.py` | Grid-анализ `alpha_pos × beta_neg` → `scenario_balance_score` |
| `tests/test_institutional_loop.py` | 6 сценарных тестов для поведения Inst |

### Изменённые файлы

| Файл | Изменение |
|------|-----------|
| `src/acmf/task_runner.py` | Добавлены задачи `institutional_loop_diagnostics` и `institutional_sensitivity` |

---

## Результаты тестов

```
32 passed, 0 failed, 0 warnings
tests/test_institutional_loop.py     6 passed
tests/test_dynamics_mechanisms.py    6 passed
tests/test_synthetic_forecast_benchmark.py  17 passed
tests/test_core.py                   3 passed
```

---

## Результаты диагностики

### Декомпозиция pull/drag (120 шагов, dt=0.5, default params)

| Сценарий | pull_total | drag_total | drag/pull |
|---|---|---|---|
| level_shift_shock_recovery | 0.0345 | 0.0413 | 1.196 |
| low_stress_trend | 0.0345 | 0.0413 | 1.196 |
| regime_change_stress | 0.0334 | 0.0402 | 1.205 |
| saturation_curve | 0.0316 | 0.0386 | 1.218 |

### Разбивка pull по компонентам (среднее по сценариям)

| Компонент | Значение | Доля |
|---|---|---|
| `pull_mental_agency` (alpha_pos * gamma_inst * M * G * (1-Inst)) | 0.0186 | ~57% |
| `pull_resilience` (alpha_pos * R * SocialCapital * (1-Inst)) | 0.0145 | ~44% |
| `pull_recovery_gate` (recovery_mode amplification) | 0.0003 | <1% |

### Разбивка drag по компонентам (среднее по сценариям)

| Компонент | Значение | Доля |
|---|---|---|
| `drag_structural_decay` (beta_neg * StructuralDecay * Inst) | ~0.026 | **~63%** |
| `drag_natural_decay` (NaturalDecay * Inst) | ~0.010 | ~24% |
| `drag_corruption` (beta_neg * Corruption * V * Inst) | ~0.006 | ~13% |

**Вывод: доминирующий drag — `StructuralDecay`, не коррупция.**

### Sensitivity grid alpha_pos × beta_neg → scenario_balance_score

```
beta_neg    0.05  0.10  0.20  0.40
alpha_pos
  0.10         1     1     1     1
  0.25         1     1     1     1
  0.50         1     1     1     1
  1.00         0     0     0     1
```

`alpha_pos = 1.00` вызывает `artificial_growth` (Inst > 0.9 более 20% шагов) → score падает.  
Рабочий диапазон: `alpha_pos ∈ [0.10, 0.50]`, любой `beta_neg`.

---

## Диагностические выходные файлы

Генерируются командами `--task institutional_loop_diagnostics` и `--task institutional_sensitivity`:

| Файл | Содержание |
|------|------------|
| `artifacts/diagnostics/institutional_loop_decomposition.csv` | Per-step pull/drag по компонентам, 4 сценария |
| `artifacts/diagnostics/institutional_sensitivity_grid.csv` | Grid alpha_pos × beta_neg, 4 сценария, behavioral criteria |

---

## Найденная проблема

> **`StructuralDecay` — основной источник inst_drag (~63%).**  
> В уравнении `dx[6]` термин `beta_neg * StructuralDecay * Inst` делит тот же коэффициент `beta_neg` с коррупцией, хотя по физике эти механизмы должны иметь разные веса.

Текущий код:
```python
dx[6] = inst_pull - (NaturalDecay + beta_neg * (Corruption * V + StructuralDecay)) * Inst
```

---

## Что не делалось (по требованиям 4.2.0)

- Нет real-data validation
- Нет full parameter calibration
- Нет joint measurement calibration

---

## Следующий шаг: 4.2.1 — StructuralDecay Fix

**Цель:** Разделить `beta_neg` и `beta_sd` (вес структурного распада) как независимые параметры:

```python
drag = (NaturalDecay + beta_neg * Corruption * V + beta_sd * StructuralDecay) * Inst
```

Добавить `beta_sd` в `ACMFParams` (default ~0.05–0.10 вместо текущих 0.20).  
Задача: достичь `inst_drag ≈ inst_pull` в `low_stress_trend` сценарии при реалистичных значениях.

---

## История релизов

| Версия | Коммит | Ключевое достижение |
|---|---|---|
| 4.0.0 | `aa75079` | Stable baseline: fast tests green, train-only scaler |
| 4.1.0 | `9935d35` | Clean target mapping: response/state benchmark разделены, recovery bell, StructuralLimits расжат |
| **4.2.0** | **`3c21c62`** | **Institutional diagnostics: drag_structural_decay идентифицирован как root cause** |

# ACMF 4.2.3 — Temporal Recovery Window
**Дата:** 2026-07-31  
**Коммит:** `(pending)`  
**Ветка:** `main`

---

## Цель релиза

Создать временное окно после shock, где `institutional pull > institutional drag` и `dInst > 0`, но только как временная recovery-фаза, без искусственного постоянного роста институтов.

---

## Что деплоилось

| Файл | Изменение |
|---|---|
| `src/acmf/core.py` | `gate_amp` default повышен с `5.0` до `10.0` |
| `scripts/run_institutional_loop_diagnostics.py` | Добавлены `detect_phases()`, `phase_summary()`, `recovery_window_stats()` и колонка `phase_label` |
| `scripts/run_institutional_sensitivity.py` | Добавлен `recovery_window_exists`, расширен `scenario_balance_score` до диапазона `-2..+4` |
| `tests/test_institutional_loop.py` | Добавлены 6 gate-тестов для 4.2.3 |

---

## Результаты тестов

`49 passed, 0 failed`

---

## Диагностика 4.2.3

### gate_amp sensitivity (80 шагов)

| gate_amp | mean_dInst | recovery_window_exists | artificial_growth | score |
|---|---:|---|---|---:|
| 1.0 | -0.003694 | True | False | 3 |
| 3.0 | -0.002900 | True | False | 3 |
| 5.0 | -0.001993 | True | False | 4 |
| **10.0** | **+0.000546** | **True** | **False** | **3** |
| 20.0 | +0.003253 | False | False | 1 |

### Phase-level (level_shift_shock_recovery, 120 шагов)

| Фаза | pull_total | drag_total | mean_dInst | gate_share |
|---|---:|---:|---:|---:|
| pre_shock | 0.06655 | 0.07112 | -0.00458 | 40.98% |
| shock | 0.07158 | 0.06778 | +0.00380 | 16.47% |
| **recovery_window** | **0.06782** | **0.06733** | **+0.00049** | **3.02%** |
| stabilization | 0.06694 | 0.06707 | -0.00013 | 0.51% |

### Recovery window stats (level_shift_shock_recovery)

- `window_exists`: **True**
- `window_length`: **28** шагов с `dInst > 0`
- `mean_dInst_in_window`: **+0.000492**
- `pull_gt_drag_fraction`: **96.55%**
- `inst_change`: **+0.00681**

---

## Вывод

Temporal recovery window достигнуто: в recoverable shock есть устойчивая положительная recovery-фаза после bottom. При этом `artificial_growth` не появился, а persistent stress остаётся различимым.


# ACMF 4.2.1 — Structural Decay Drag Separation
**Дата:** 2026-07-31  
**Коммит:** `(pending)`  
**Ветка:** `main`

---

## Цель релиза

Разделить institutional negative drag на два независимых канала:
- `beta_neg` — corruption/political institutional drag
- `beta_sd` — structural decay drag (новый параметр)

Убрать систематическое доминирование StructuralDecay без искусственного усиления positive pull.

---

## Что деплоилось

### Изменённые файлы

| Файл | Изменение |
|------|-----------|
| `src/acmf/core.py` | Добавлен параметр `beta_sd=0.08`; формула `dx[6]` разделена на два drag-канала |
| `scripts/run_institutional_loop_diagnostics.py` | `drag_structural_decay` теперь использует `beta_sd`, не `beta_neg` |
| `scripts/run_institutional_sensitivity.py` | Добавлена функция `run_beta_sd_sensitivity()`, новый режим `--mode beta_sd/all`, новый CSV `institutional_beta_sd_sensitivity.csv` |
| `tests/test_institutional_loop.py` | Добавлены 5 Gate Tests (Gate 1–5) |

### Изменение в core.py

**До:**
```python
dx[6] = inst_pull - (NaturalDecay + beta_neg * (Corruption * V + StructuralDecay)) * Inst
```

**После:**
```python
inst_drag_corruption = beta_neg * Corruption * V * Inst
inst_drag_structural = beta_sd * StructuralDecay * Inst
dx[6] = inst_pull - (NaturalDecay * Inst + inst_drag_corruption + inst_drag_structural)
```

### Новый параметр `beta_sd`

| Поле | Значение |
|------|----------|
| Default | `0.08` |
| Expected range | `0.02 – 0.20` |
| Status | diagnostic parameter, not yet empirically calibrated |
| Rationale | structural decay is slower than corruption-driven degradation |
| Previous implicit value | `0.20` (shared `beta_neg` — was methodologically wrong) |

---

## Результаты тестов

```
37 passed, 0 failed
tests/test_institutional_loop.py     11 passed (6 prior + 5 new Gate tests)
tests/test_dynamics_mechanisms.py     6 passed
tests/test_core.py                    3 passed
```

---

## Gate Tests — Все пройдены ✓

| Gate | Критерий | Результат |
|------|----------|-----------|
| Gate 1 | StructuralDecay share < 50% | **42.6%** ✓ (было 63%) |
| Gate 2 | No artificial growth at beta_sd=0.08 | **0/4 сценариев** ✓ |
| Gate 3 | No artificial growth globally | **0/4 сценариев** ✓ |
| Gate 4 | Persistent stress remains possible | mean_dInst < 0 в regime_change ✓ |
| Gate 5 | Lower beta_sd ≥ higher beta_sd score | 1 ≥ 1 ✓ |

---

## Результаты диагностики

### Pull/drag decomposition (120 шагов, beta_sd=0.08, alpha_pos=0.25, beta_neg=0.20)

| Сценарий | pull_total | drag_total | drag/pull | drag_structural | share |
|---|---|---|---|---|---|
| level_shift_shock_recovery | 0.05602 | 0.05689 | **1.015** | 0.02424 | **42.6%** |
| low_stress_trend | 0.05602 | 0.05689 | **1.015** | 0.02424 | **42.6%** |
| regime_change_stress | 0.05360 | 0.05480 | **1.022** | 0.02321 | **42.4%** |
| saturation_curve | 0.04966 | 0.05138 | **1.034** | 0.02142 | **41.7%** |

**Сравнение с 4.2.0:**

| Метрика | 4.2.0 | 4.2.1 | Δ |
|---|---|---|---|
| drag/pull ratio | 1.196–1.218 | 1.015–1.034 | **−0.18 (−15%)** |
| StructuralDecay share | ~63% | ~42% | **−21 п.п.** |
| pull_total | 0.032–0.035 | 0.050–0.056 | **+0.018 (+54%)** |

> Разделение параметра не только уменьшило drag, но и позволило pull возрасти — благодаря тому, что `beta_neg` больше не подавлял `SocialCapital` косвенно через drag balance.

### beta_sd sensitivity (alpha_pos=0.25, beta_neg=0.20, 60 шагов)

| beta_sd | mean_dInst | recovery_detected | artificial_growth | score |
|---|---|---|---|---|
| **0.03** | **+0.0028** ✓ | False | False | 1 |
| **0.08** (default) | -0.0065 | False | False | 1 |
| 0.15 | -0.0125 | False | False | 1 |
| 0.25 | -0.0149 | False | False | 1 |

**Ключевой вывод:** При `beta_sd=0.03` mean_dInst становится положительным (+0.003) — первый раз когда Inst начинает медленно расти. Это задаёт диапазон для следующей калибровки.

### Sensitivity grid alpha_pos × beta_neg → scenario_balance_score

```
beta_neg    0.05  0.10  0.20  0.40
alpha_pos
  0.10         1     1     1     1
  0.25         1     2     1     1   ← best combo
  0.50         1     1     1     1
  1.00         0     0     0     0   ← artificial growth
```

**Лучшая комбинация: alpha_pos=0.25, beta_neg=0.10 → score=2**  
(Единственная комбинация с score=2 — получила +1 за recovery_detected в level_shift сценарии)

---

## Что пока не исправлено

- `recovery_detected` = False во всех комбинациях (кроме alpha_pos=0.25, beta_neg=0.10) — recovery по-прежнему слабый
- mean_dInst отрицательный при default beta_sd=0.08 → Inst медленно деградирует
- `pull_recovery_gate` = 0.0007 — recovery-mode gate (P3) всё ещё почти не работает

---

## Что не делалось (по требованиям 4.2.x)

- Нет real-data validation
- Нет full parameter calibration
- Нет joint measurement calibration

---

## Следующий шаг: 4.2.2 — Recovery Gate Activation

Механизм P3 (recovery_mode_gate) даёт лишь 0.1% от pull_total. Возможные причины:
1. `dx[7]` (dR/dt) почти всегда ≈ 0 → gate = 0
2. `alpha_rec` делитель слишком большой
3. Начальное состояние R=0.5 не генерирует заметного recovery signal

**Задача 4.2.2:** диагностировать, почему dR/dt мало в diagnostic scenarios, и настроить recovery signal threshold.

---

## Диагностические выходные файлы

| Файл | Содержание |
|------|------------|
| `artifacts/diagnostics/institutional_loop_decomposition.csv` | Per-step decomposition, 4.2.1 values |
| `artifacts/diagnostics/institutional_sensitivity_grid.csv` | alpha_pos × beta_neg grid + beta_sd column |
| `artifacts/diagnostics/institutional_beta_sd_sensitivity.csv` | beta_sd grid [0.03, 0.08, 0.15, 0.25] |

---

## История релизов

| Версия | Коммит | Ключевое достижение |
|---|---|---|
| 4.0.0 | `aa75079` | Stable baseline: fast tests green, train-only scaler |
| 4.1.0 | `9935d35` | Clean target mapping, recovery bell, StructuralLimits расжат |
| 4.2.0 | `3c21c62` | Institutional diagnostics: drag_structural_decay = root cause |
| **4.2.1** | **`(pending)`** | **beta_sd разделён; drag/pull 1.20 → 1.015; StructuralDecay share 63% → 42%** |

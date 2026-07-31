# ACMF 4.2.2 — Recovery Gate Activation
**Дата:** 2026-07-31  
**Коммит:** `(pending)`  
**Ветка:** `main`

---

## Цель релиза

Сделать recovery-mode gate функциональным — заметным механизмом institutional pull,  
а не декоративным (~0.1% вклада как в 4.2.1).

**Целевой диапазон:** recovery gate доля от pull_total ≥ 5% в shock-recovery сценарии.

---

## Корень проблемы (диагностировано в 4.2.2)

Формула до 4.2.2:
```python
recovery_mode_gate = smax(0.0, dx[7]) / (alpha_rec + EPSILON)
```

`dx[7]` (dR/dt) типично = 0.004–0.006 при default параметрах.  
Делитель `alpha_rec = 0.25` → gate ≈ 0.018.  
Умножается на `R * SocialCapital * (1-Inst)` ≈ 0.5 * 0.27 * 0.5 = 0.068.  
Итог: pull_recovery_gate ≈ 0.25 * 0.068 * 0.018 = **0.0003 — декоративно**.

---

## Что деплоилось

### Изменённые файлы

| Файл | Изменение |
|------|-----------|
| `src/acmf/core.py` | Добавлен `gate_amp=5.0`; формула gate умножается на `gate_amp` |
| `scripts/run_institutional_loop_diagnostics.py` | gate использует `gate_amp`; добавлены `recovery_gate_share_by_scenario()`, `recovery_phase_stats()` |
| `scripts/run_institutional_sensitivity.py` | Добавлена `run_gate_amp_sensitivity()`; новый режим `--mode gate_amp` |
| `tests/test_institutional_loop.py` | 6 новых Gate Tests (4.2.2 Gates 1–5 + CSV export) |

### Изменение в core.py

**До:**
```python
recovery_mode_gate = smax(0.0, dx[7]) / (alpha_rec + EPSILON)
```

**После:**
```python
# gate_amp rescales dx[7] so recovery-mode gate is functionally significant (~5-15% of pull)
recovery_mode_gate = smax(0.0, dx[7]) * gate_amp / (alpha_rec + EPSILON)
```

### Новый параметр `gate_amp`

| Поле | Значение |
|------|----------|
| Default | `5.0` |
| Expected range | `1.0 – 20.0` |
| Status | diagnostic parameter, not yet empirically calibrated |
| Rationale | rescales dR/dt signal to give gate functional significance |
| Effect at gate_amp=1 (old) | gate share ~1.2% of pull |
| Effect at gate_amp=5 (new) | gate share ~6.5% of pull |

---

## Результаты тестов

```
26 passed, 0 failed
tests/test_institutional_loop.py     17 passed (11 prior + 6 new)
tests/test_dynamics_mechanisms.py     6 passed
tests/test_core.py                    3 passed
```

---

## Gate Tests — Все пройдены ✓

| Gate | Критерий | Результат |
|------|----------|-----------|
| Gate 1 | recovery_gate_share ≥ 5% в shock scenario | **6.5%** ✓ (было 1.2%) |
| Gate 2 | No artificial growth при gate_amp=5.0 | **0/4 сценариев** ✓ |
| Gate 3 | recovery phase min drag/pull < 1.1 | **1.000** ✓ (drag = pull!) |
| Gate 4 | regime_change_stress mean_dInst < 0.01 | **-0.004** ✓ |
| Gate 5 | StructuralDecay share < 55% | **42.4%** ✓ |

---

## Результаты диагностики

### Pull/drag decomposition (120 шагов, gate_amp=5.0, beta_sd=0.08)

| Сценарий | pull_total | drag_total | drag/pull | gate_share |
|---|---|---|---|---|
| level_shift_shock_recovery | 0.06233 | 0.06235 | **1.000** | **6.5%** |
| low_stress_trend | 0.06233 | 0.06235 | **1.000** | **6.5%** |
| regime_change_stress | 0.05988 | 0.06022 | **1.006** | **6.4%** |
| saturation_curve | 0.05546 | 0.05633 | **1.016** | **6.1%** |

**Прогресс через версии:**

| Метрика | 4.2.0 | 4.2.1 | 4.2.2 |
|---|---|---|---|
| drag/pull ratio | 1.20 | 1.015 | **1.000** |
| StructuralDecay share | 63% | 42% | **42%** |
| pull_recovery_gate share | ~1% | ~1.2% | **6.5%** |
| pull_total | 0.033 | 0.056 | **0.062** |

### gate_amp sensitivity (alpha_pos=0.25, beta_neg=0.20, beta_sd=0.08, 60 шагов)

| gate_amp | mean_dInst | recovery_detected | artificial_growth | score |
|---|---|---|---|---|
| 1.0 | -0.0065 | False | False | 1 |
| 3.0 | -0.0054 | False | False | 1 |
| **5.0 (default)** | **-0.0041** | False | False | **1** |
| **10.0** | **≈ 0.000** | False | False | **2** ← optimal balance |
| 20.0 | +0.006 | False | False | 1 |

**Ключевые наблюдения:**
- `gate_amp=10.0` даёт mean_dInst ≈ 0 (полный баланс pull ≈ drag) и score=2 — лучший результат
- `gate_amp=5.0` (default) близко к балансу, консервативнее
- `gate_amp=20.0` даёт положительный dInst, но всё ещё без artificial growth за 60 шагов
- `recovery_detected` остаётся False — recovery в level_shift всё ещё недостаточен для обнаружения

---

## Что пока не исправлено

- `recovery_detected = False` во всех комбинациях — подъём Inst после шока не детектируется
  - drag/pull = 1.000 означает quasi-equilibrium, а не реальный recovery
  - Для recovery нужен **временный overcorrection** pull > drag в окне после шока
- `gate_amp=10` даёт лучший scenario_balance_score (2) но не включён как default — требует проверки на longer runs

---

## Что не делалось

- Нет real-data validation
- Нет full parameter calibration  
- Нет joint measurement calibration

---

## Следующий шаг: 4.2.3 — Temporal Recovery Window

Нужно, чтобы в `level_shift_shock_recovery` после bottom phase Inst **реально поднимался** (dInst > 0 в recovery window), а не просто балансировался при drag ≈ pull.

Гипотеза: нужен временный импульс positive pull, зависящий от истории stress  
(shock depth → recovery amplitude). Варианты:
1. Повысить `gate_amp` до 10 и добавить более длинные runs (120+ шагов) для детекции
2. Добавить "recovery momentum" — переменную с памятью о глубине shock
3. Усилить `alpha_pos` только в transition phase (условно через stress gradient)

---

## Диагностические выходные файлы

| Файл | Содержание |
|------|------------|
| `artifacts/diagnostics/institutional_loop_decomposition.csv` | Per-step decomposition с gate_amp=5.0 |
| `artifacts/diagnostics/institutional_gate_amp_sensitivity.csv` | gate_amp grid [1,3,5,10,20] |

---

## История релизов

| Версия | Коммит | Ключевое достижение |
|---|---|---|
| 4.0.0 | `aa75079` | Stable baseline |
| 4.1.0 | `9935d35` | Clean target mapping, recovery bell, StructuralLimits расжат |
| 4.2.0 | `3c21c62` | Institutional diagnostics: drag_structural_decay = root cause |
| 4.2.1 | `c1b93b7` | beta_sd разделён; drag/pull 1.20→1.015 |
| **4.2.2** | **`(pending)`** | **gate_amp=5: gate share 1%→6.5%; drag/pull 1.015→1.000** |

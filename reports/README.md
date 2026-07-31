# ACMF Release Reports

Каждый релиз сопровождается отчётом с описанием изменений, результатов тестов и диагностики.

## Конвенция именования

```
acmf_{version}_{short_description}_report.md
```

| Часть | Пример | Описание |
|---|---|---|
| `version` | `420` | Версия без точек: 4.2.0 → `420` |
| `short_description` | `institutional_loop_diagnostics` | snake_case, 3–5 слов |

### Примеры
```
acmf_400_stable_baseline_report.md
acmf_410_dynamics_diagnostic_benchmark_report.md
acmf_420_institutional_loop_diagnostics_report.md
acmf_421_structural_decay_fix_report.md
```

## Структура отчёта

Каждый отчёт должен содержать:

1. **Цель релиза** — в 1-2 предложениях
2. **Что деплоилось** — новые и изменённые файлы
3. **Результаты тестов** — счётчик passed/failed
4. **Диагностические результаты** — числа, таблицы, выводы
5. **Найденные проблемы** — что обнаружено, что ещё не исправлено
6. **Что не делалось** — явное перечисление ограничений
7. **Следующий шаг** — конкретная задача для следующего релиза
8. **История релизов** — накапливающаяся таблица

## Все отчёты

| Файл | Версия | Краткое содержание |
|---|---|---|
| [acmf_420_institutional_loop_diagnostics_report.md](acmf_420_institutional_loop_diagnostics_report.md) | 4.2.0 | drag_structural_decay = root cause inst degradation |
| [acmf_421_structural_decay_drag_separation_report.md](acmf_421_structural_decay_drag_separation_report.md) | 4.2.1 | beta_sd separated; drag/pull 1.20→1.015; SD share 63%→42% |

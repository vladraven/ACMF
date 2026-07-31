# Отчёт об исправлениях (внешний аудит, не входит в оригинальный репозиторий)

Состояние на момент клонирования (`main`, коммит `00c1c8a`): **9 из 19 тестовых
модулей не импортировались**, 2 теста падали. Причина — коммит `a633e56`
("3.3.1.9 clean quality hardening package") удалил ~680 строк реализации из
`multiscale.py`, `observation_designer.py`, `calibration.py`,
`data_fetchers/world_bank.py`, не обновив ни тесты, ни зависимые модули.
Собственные отчёты проекта (`acmf_3319_...md`, `acmf_33110_...md`) утверждали
"15 passed", "no stub occurrences" — оба утверждения были неверны на момент
проверки.

## Что сделано

1. **multiscale.py** — восстановлена полная версия из истории git (до коммита
   `a633e56`): `aggregate_children`, `disaggregate_parent_to_children`,
   `compare_scales`, `save/load_multiscale_frame`.
2. **observation_designer.py** — восстановлена полная версия
   (`greedy_observation_design`, `minimal_observation_set`,
   `design_for_world_panel_country`, `result_to_dict`), работающая с 12-параметрической
   моделью `ACMFObjective`. Добавлена отдельная лёгкая функция
   `score_candidate_observables_simple`, совместимая с новым 8-параметрическим
   `calibrate_country_proxy` — используется `empirical_validation.py`.
3. **identifiability.py** — восстановлена полная версия
   (`parameter_sensitivity_matrix`, `fisher_information_matrix`,
   `fim_diagnostics`, `parameter_correlation_from_fim`, `top_correlated_pairs`,
   `observation_design_score`, `windowed_identifiability`). Добавлены
   `simple_sensitivity_matrix` / `simple_fim_diagnostics` — облегчённый вариант
   под новый calibration API, используемый `empirical_validation.py`.
4. **calibration.py** — новый (solver-based, 8-параметрический)
   `calibrate_country_proxy`/`predict_from_theta` оставлен без изменений
   (от него зависит рабочий `empirical_validation.py`). Дополнительно
   восстановлены `LossConfig`, `PriorSpec`, `ACMFObjective` — от них зависят
   `identifiability.py`, `observation_designer.py`, `real_identifiability.py`.
   Обе линии теперь сосуществуют под разными именами.
5. **real_identifiability.py** — восстановлена полная версия из истории.
6. **data_fetchers/world_bank.py** — добавлена обёртка `fetch_world_bank`
   (backends `requests`/`wbdata`/`auto`) поверх нового `fetch_world_bank_requests`,
   от неё зависят `panel_builder.py`/`data_cube.py`.
7. **world_panel.py** — добавлены `world_panel_profile`, `top_countries_by_coverage`,
   `ID_COLUMNS` (нужны тестам и отчётности), без изменения существующего
   `make_acmf_proxy_panel`/`state_from_proxy`.
8. **data_fetchers/wgi.py** — убрана заглушка `return pd.DataFrame()`
   (дважды), заменена на `raise ManualDownloadRequired(...)` — приведено
   в соответствие с контрактом, который проект сам декларирует в
   `docs/QUALITY_HARDENING.md`.
9. **__init__.py** — экспортированы `adaptive_dynamics_layer`, `LossConfig`,
   `world_panel_profile`, `top_countries_by_coverage`; поправлена
   несостыковка версии в докстринге (было "3.3.1.8", `__version__` — "3.3.1.10").
10. **MANIFEST.txt** — добавлены `README_DEPLOY.md` и
    `data/world_data_1995_2025.csv`, которые требует собственный тест проекта.
11. Устаревшие проверки версии в 3 тестах (`assert __version__ ==
    '3.3.1.7-clean-multiscale'`) заменены на сверку с текущим `__version__`
    пакета — раньше они были жёстко привязаны к версии за три релиза до
    текущей и гарантированно проваливались бы после любого будущего апдейта
    версии.

## Что НЕ исправлено (осознанно)

- **Параметры модели** (`core.py`) — 39 из ~65 параметров имеют значение
  ровно `0.2`; источника калибровки или ссылки на данные в репозитории нет.
  Это не баг кода, а нефундированные константы модели — их "исправление"
  потребовало бы полноценной эмпирической калибровки, а не патча кода.
- **Диагностика идентифицируемости в `empirical_validate_core5`** — при
  колоссальных condition number (1e11–1e15) отчёт показывает
  `weak_parameters: 0`. Это унаследованная логика классификации из
  `empirical_validation.py` (порог 0.25/0.75 на CV параметра, а не на
  condition number) — технически работает как написано, но вводит в
  заблуждение относительно реальной идентифицируемости. Не трогал, так как
  это вопрос методологии, а не сломанного кода.

## Проверка

```
python3 -m pytest tests/ -q      # 49 passed (двойной прогон подтверждён)
python3 main.py --task health
python3 main.py --task empirical_validate_canada
python3 main.py --task empirical_validate_core5
python3 main.py --task empirical_indicator_ablation
python3 main.py --task empirical_backtest_2008
```
Все пять задач и полный набор тестов проходят на чистом клоне этого архива.

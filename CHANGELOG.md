# CHANGELOG · MindDock-OS
> История проекта. Читать с конца — последнее сверху.
> Формат: [Роль] что произошло

---

## 2026-06-13

### Торговля
- [Analyst] gaussian_mm · Europe убыток · USA +$1.06 · Night +$0.55
- [Analyst] Паттерн подтверждён: Гаусс любит волатильность USA и тихую азию
- [Risk] pmm_dynamic остановлен · gaussian_mm запущен на замену
- [Analyst] session_monitor (Gemini) собирает статистику автоматически ✅

### MindDock OS
- [Architect] MindDock-OS репо создан на GitHub
- [Architect] MindDockOS.ipynb · Cell 1-8 sealed · реактивный цикл работает
- [Architect] render_browser() · карта системы открывается в браузере
- [Architect] Принцип зафиксирован: MindDock не хранит знания — хранит карту
- [Algo-Dev] Help Engine реализован · cmd("help"), cmd("status"), cmd("focus")
- [DevOps] GitHub push · quants-lab · 83 файла · история кода сохранена

## 2026-06-12

### Торговля
- [Analyst] gaussian_mm запущен на реале · 1000PEPE-USDC · leverage=20
- [Risk] pmm_dynamic · 94% EARLY_STOP · time_limit=7200 · проблема зафиксирована
- [Analyst] Варианты A/B/C для fix EARLY_STOP готовы → отложено

### MindDock OS
- [Architect] Концепция MindDock OS сформулирована
- [Architect] Три уровня памяти: PROJECT_CONTEXT · NAVIGATOR · SESSION_LOG
- [Architect] Матрица ролей: Quant · Algo-Dev · DevOps · Risk · Analyst · Instructor · Architect
- [Architect] MISSION: открытая лаборатория · новый участник за 1 день в теме
- [DevOps] Инфраструктура проверена · 7 Docker контейнеров · endpoints задокументированы

---

## Протокол новой сессии
1. Прочитай последние 5 строк CHANGELOG.md
2. Загрузи PROJECT_CONTEXT.md + SESSION_LOG.md
3. Напиши: "Продолжаем. Фокус: [Роль] [задача]"

## Открытые вопросы
- [ ] PostgreSQL :5432 — что хранится?
- [ ] EARLY_STOP fix для gaussian_mm — варианты A/B/C
- [ ] scan_project() — автонаполнение карты
- [ ] minddock_core.py — финальная сборка
- [DevOps] session_stats.py путь: ~/condor/trading_agents/session_monitor/routines/

## 2026-06-14

### База данных — уточнение
- MongoDB ЖИВАЯ: quants_lab → коллекция "experiments" (3-4 записи, EXP_001/optuna)
- Предыдущая проверка через mongosh показала [] — вероятно смотрели через другое подключение/контейнер
- TODO: найти скрипт который пишет в experiments, сверить с mongosh

### Железо — ограничение проекта
- MacBook Pro 11,2 (2014) · Intel i7 2.2GHz · 4 ядра · 16GB RAM
- Docker Desktop 4.20.1 (устаревший)
- Решение: обновлять Condor осторожно, поэтапно, с проверкой нагрузки на каждом шаге

### Condor — точка входа найдена
- Запуск: `cd ~/condor && python3 main.py`
- Использует системный Python 3.12 (НЕ conda env)
- Процесс работает непрерывно 3+ дня без перезапуска
- Порт 8088, PID меняется при каждом запуске

### Бэкап перед обновлением Condor
- Путь: ~/condor_backup_20260614 (1.1GB)
- Текущая версия: be542cf, отстаёт на 90 коммитов от origin/main
- Локальные изменения НЕ закоммичены: routine_store.py, web/models.py, pyproject.toml, uv.lock
- Неотслеживаемые (важные, наши): routines/session_stats.py, routines/position_summary.py, routines/update_bot_config.py, trading_agents/

## 2026-06-14 — Обновление Condor: УСПЕШНО

### Что сделано
- Бэкап: ~/condor_backup_20260614 (1.1GB)
- Локальные изменения сохранены: ~/MindDock-OS/knowledge/condor_local_changes_20260614/diff_before_update.patch
- git pull: 90 коммитов, fast-forward, без конфликтов
- Проблема: onnxruntime (через faster-whisper) не имеет колеса под macOS Intel x86_64
- Решение: убрана зависимость faster-whisper из pyproject.toml (строка 21) — нужна только для voice/transcribe, не используется в торговле
- uv sync прошёл успешно (197 пакетов)
- hummingbot-api-client: 1.4.1 -> 1.5.3
- numpy: 1.26.4 -> 2.4.2

### Запуск Condor (важно!)
ПРАВИЛЬНО:   cd ~/condor && uv run python3 main.py
НЕПРАВИЛЬНО: cd ~/condor && python3 main.py  (ModuleNotFoundError: telegram)

### Результат
- Condor запущен, порт 8088, WebSocket работает
- Наши файлы целы: routines/session_stats.py, position_summary.py, update_bot_config.py, trading_agents/session_monitor/
- Новые фичи доступны: AggregatedPnlChart, ControllerPnlChart, BotRunsTab, routine_hooks
- Боты: 0 запущено (специально остановлены перед обновлением)

### TODO следующая сессия
- Открыть localhost:8088 в браузере, проверить UI
- Запустить gaussian_mm заново
- Проверить новые вкладки (BotRuns, AggregatedPnl)

## НАЙДЕНА РЕАЛЬНАЯ БАЗА ДАННЫХ — 2026-06-14

### PostgreSQL hummingbot_api (порт 5432, контейнер hummingbot-postgres)
Подключение: `docker exec -it hummingbot-postgres psql -U hbot -d hummingbot_api`

14 таблиц. ГЛАВНАЯ:
- controller_performance_snapshots: 6034 записей, диапазон 2026-06-01 -> 2026-06-14 (13 дней!)
  -> 5-минутные снимки PnL/volume/positions для ВСЕХ контроллеров за весь период
  -> ЭТО НОВАЯ ФИЧА из обновления Condor (controller_performance.py)
- bot_runs: 62 запуска ботов
- executors, orders, trades: пусто (0) — данные по-прежнему в SQLite файлах

### API доступ (без прямого psql)
- GET /bot-orchestration/controller-performance-latest
- GET /bot-orchestration/controller-performance-history?interval=5m

### Обнаружена стратегия SOL-dynamic-v8_SOL (не отслеживали в TRADING_LOG!)
- bot_20260601003000: realized +0.97 USDT, EARLY_STOP=1983, SL=6, TP=33
- bot_20260601125631: realized +3.91 USDT, volume 6257 USDT

### MongoDB quants_lab — подтверждено НЕ используется
- experiments в коде = .md файлы (trading_agent/dry_runs/), не Mongo
- quants_lab пуста

### TODO следующая сессия
- Выгрузить controller_performance_snapshots за 13 дней -> TRADING_LOG
- Построить полную картину по всем ботам (не только gaussian_mm)
- Решить судьбу MongoDB: убрать или найти применение

## MongoDB — закрыт вопрос
MongoDB (quants_lab) = часть quants-lab framework (не наше изобретение).
Используется: app/tasks/deployment/*, app/tasks/quantitative_methods/cointegration/*
Назначение: stat_arb, coint deployment tasks.
Статус: не используется (мы работаем через Condor), решение - НЕ ТРОГАТЬ, оставить готовой к будущему использованию.
6 подключений = локальные (mongo-express + системные), не тревожно.

## [Risk/Quant] КЛЮЧЕВАЯ НАХОДКА — 2026-06-16

### Главное: pmm-dynamic-best-v8 — ЕДИНСТВЕННАЯ доказанно прибыльная конфигурация
- bot: bot_20260601003000-20260601-003457
- controller_id: pmm-dynamic-best-v8
- Период: 2026-06-01 00:40 -> 2026-06-04 09:25 (running)
- PnL: $0 -> +$76 на $100 капитала за 3 дня (06-01: +18.98, 06-02: +59.56, 06-03: +75.98)
- 06-04: резкий сброс с пика 76.25 до 15.89 (вероятно рестарт/закрытие, не органический убыток)

### Все остальные конфигурации после v8 — около нуля или в минусе
gaussian-*, PEPE-dynamic_PEPE_real_USDC, PEPE-USDC_true и др. (06-04 -> 06-15)
НИ ОДНА не повторила паттерн v8.

### SOL-dynamic-v8_SOL — тоже был в плюсе 06-01/03 (до +9.55), 
но 06-04 КАТАСТРОФА: -56.07 за один день (разовый обвал, не постепенный).

## СЛЕДУЮЩАЯ СЕССИЯ — НАЧАТЬ С ЭТОГО:

1. Найти конфиг bot_20260601003000-20260601-003457 / pmm-dynamic-best-v8:
   - Condor configs, ~/condor_backup_20260614, git history до 06-04
   - find / grep по "pmm-dynamic-best-v8" в ~/condor

2. Понять ПОЧЕМУ от v8 отказались 04.06 — что произошло в 09:25:
   - проверить логи бота за 06-04 09:00-10:00
   - проверить SOL-dynamic-v8_SOL за тот же момент (-56 убыток тоже 06-04!)
   - ГИПОТЕЗА: общий инцидент 06-04 (сбой/рестарт системы) затронул оба v8-бота одновременно

3. Если конфиг найден и инцидент объяснён — РЕСТАРТ v8 с тем же конфигом 
   приоритетнее любых новых тестов/гипотез A/B/C.

НЕ ТРОГАТЬ: гипотезы A/B/C для pmm_dynamic EARLY_STOP, regime classifier,
walk-forward testing — всё это менее приоритетно чем восстановление 
proven-working конфига v8.

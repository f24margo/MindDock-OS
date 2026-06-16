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

## [Quant] Найден pmm-dynamic-best-v8.yml — 2026-06-16
Файл: pmm_dynamic/pmm-dynamic-best-v8.yml
ВНИМАНИЕ: в файле connector=binance_perpetual_testnet, trading_pair=BTC-USDT,
НО реально торговался как controller_id=pmm-dynamic-best-v8 на 1000PEPE-USDC
(bot_20260601003000, +76% за 3 дня). Видимо параметры адаптированы при деплое,
сам YAML - референсный шаблон, не точная копия живого конфига.

ПОДТВЕРЖДЁН ПАТТЕРН v8-семьи (best-v8, SOL-v8):
- spreads ШИРОКИЕ: 0.43-1.48 (vs текущий боевой 0.001-0.0025)
- executor_refresh_time: 45-70 (vs текущий 20)
- macd_slow: 180 (vs текущий 26)
- stop_loss: 0.005 (vs текущий 0.015)

ГИПОТЕЗА УСИЛЕНА: текущий боевой конфиг pmm_dynamic (PEPE, узкие spreads,
быстрый refresh) - принципиально другая, проигрывающая логика по сравнению
с proven v8.

СЛЕДУЮЩАЯ СЕССИЯ:
1. Найти точный конфиг бота bot_20260601003000 (логи запуска, Condor history,
   ~/condor_backup_20260614) - именно ТЕ параметры на PEPE-USDC
2. Если не найдён - собрать гибрид: взять spread/refresh/macd_slow/natr 
   паттерн из v8-семьи + применить к PEPE-USDC/1000PEPE-USDC
3. Backtest гибрида на данных 06-01/04 (период когда v8 реально работал)
   для верификации, прежде чем на реал

## [Risk] ИСПРАВЛЕНИЕ — best-v8 НЕ был прибылен на реале — 2026-06-16
ОТМЕНА предыдущей записи "best-v8 - proven +76% за 3 дня".

УТОЧНЕНИЕ от Mykola: +76% в controller_performance_snapshots (06-01/04) -
вероятно TESTNET/бэктест результат (в файле connector=binance_perpetual_testnet).
best-v8 был запущен на РЕАЛЕ с этими же параметрами -> УБЫТОК.
После этого параметры начали менять (отсюда текущий боевой конфиг
с узкими spreads 0.001-0.0025 - попытка исправить минус от v8).

ВЫВОД: v8-паттерн (широкие spreads 0.43-1.48, refresh 45-70, macd_slow 180)
- НЕ подтверждённое решение, это исходная точка которая ПРОВАЛИЛАСЬ на реале.
Текущие узкие конфиги - результат попыток фикса, тоже не сработавших.

СТАТУС: оба направления (широкие и узкие spreads) дали убыток на реале.
Подозрение смещается на сам разрыв testnet/backtest vs real -
(slippage, fills, funding на binance_perpetual реальном vs testnet/симуляции).

СЛЕДУЮЩАЯ СЕССИЯ - НЕ повторять "найти proven конфиг".
Вместо этого: найти ЛОГИ запуска best-v8 НА РЕАЛЕ (не testnet) -
посмотреть какой именно был фактический PnL и причина минуса,
сравнить с testnet-результатом за тот же период параметров.

## [DevOps] Testnet ПОДКЛЮЧЁН УСПЕШНО — 2026-06-16
binance_perpetual_testnet добавлен в master_account.
Подтверждено: ["binance_perpetual","binance_perpetual_testnet"]

Ключи (demo Binance testnet):
- api_key: 8IzxTA1Ej5pgzsKhfWGXKDB58rx5LKtXK90j8FD6YUVLyBvrpWRz3amZ3gHXqTft
- api_secret: T8xJWnsoXHFAHAmXUbKI1qM0lRRNeG747H286FIEeX4zQlUyjvUdPywUmnqkcKGQ

Что сработало (финальная команда):
POST http://localhost:8000/accounts/add-credential/master_account/binance_perpetual_testnet
-H "Content-Type: application/json"
-u admin:admin
{"binance_perpetual_testnet_api_key": "...", "binance_perpetual_testnet_api_secret": "..."}

Почему предыдущие попытки провалились:
1. Неправильные имена полей (не знали точных названий)
2. Неправильный JSON (пропущено имя ключа в теле запроса)
3. Поля найдены через: docker exec hummingbot-api cat .../binance_perpetual_utils.py

СЛЕДУЮЩАЯ СЕССИЯ — testnet готов:
1. Открыть pmm-dynamic-best-v8.yml
2. Изменить connector: binance_perpetual_testnet, trading_pair: подобрать
3. Задеплоить через Condor :8088 и наблюдать live без риска реальных денег
4. Сравнить testnet PnL с историческим (controller_performance_snapshots)

## [Quant] Гипотеза: пересмотр методики Optuna — зафиксировано 2026-06-16
Приоритет: СРЕДНИЙ (не следующая сессия, но обязательно в ближайших)

ОТКРЫТИЕ (из Pine Script симулятора APEX PMM Studio):
Результат бэктеста критически чувствителен к шагу спреда.
Разница spread=0.0015 vs 0.0018 (20%) даёт кардинально разный PnL.
Текущий шаг Optuna вероятно слишком грубый — пропускает оптимальную зону.

ЧТО ПЕРЕСМОТРЕТЬ:
1. Шаг спреда: step=0.0001 вместо 0.001 (на порядок мельче)
   suggest_float("spread", 0.0005, 0.005, step=0.0001)
2. trailing_stop + take_profit оптимизировать СОВМЕСТНО со спредом
   (они зависимы — широкий спред требует другого TP уровня)
3. Целевая функция: добавить штраф за EARLY_STOP
   objective = total_pnl - 0.1 * early_stop_count
4. Логарифмическая шкала для спредов (log=True) — плотнее исследует
   малые значения где находится оптимальная зона

КОНТЕКСТ: спред — не один из параметров, а ГЛАВНЫЙ параметр PMM.
MACD/NATR влияют слабее. Optuna должна исследовать спред с максимальной
точностью, остальное — вторично.

## [DevOps] Итог сессии 2026-06-16 — полный путь

### Что сделано
1. Подтверждён testnet: binance_perpetual_testnet подключён, свечи чистые
2. Созданы два конфига через API:
   - PEPE-test-wide-v8: 1000PEPE-USDC, spreads 0.83/1.48, refresh 45, macd_slow 180
   - PEPE-test-narrow-v1: 1000PEPE-USDT, spreads 0.001/0.0025, refresh 20, macd_slow 26
3. Первый деплой (pepe-ab-test) провалился: total_amount_quote=15 → $3.75/ордер < min $5
4. Второй деплой (pepe-ab-test2-20260616-034224) на testnet — РАБОТАЕТ
   Positions(2) открыты, Open Orders(28) активны, свечи нормальные

### Известные косяки конфигов (исправить в следующей итерации)
- trailing_stop activation_price (0.018) > take_profit (0.002) — никогда не сработает
- stop_loss=0.005 при wide spreads 0.83 — ликвидация раньше чем TP
- candles_connector=binance_perpetual (реал) при connector=testnet — ОК, это правильно

### Минимальный notional для 1000PEPE-USDC на Binance Perpetual
Минимум $5 на ордер. Формула: total_amount_quote × 0.5 × 0.5 = размер ордера
Для min $5: total_amount_quote >= 20. Безопасно: 30+

### Проверка результатов (через 6-12ч)
docker exec hummingbot-postgres psql -U hbot -d hummingbot_api -c "
SELECT controller_id, COUNT(*) as snapshots,
(array_agg((performance::json->>'global_pnl_quote')::float 
  ORDER BY timestamp DESC))[1] as pnl_end,
(array_agg(performance::json->>'close_type_counts' 
  ORDER BY timestamp DESC))[1] as close_types
FROM controller_performance_snapshots
WHERE controller_id IN ('PEPE-test-wide-v8','PEPE-test-narrow-v1')
GROUP BY controller_id;" | cat

### Остановка бота если нужно
curl -s -X POST "http://localhost:8000/bot-orchestration/stop-instance/pepe-ab-test2-20260616-034224" \
  -u admin:admin | cat

### Testnet нестабильность — известная проблема
Binance Futures Testnet периодически деградирует: свечи на полэкрана,
интервалы 15-20 минут. Сейчас чистый — мониторить.
Если деградирует: остановить, перейти на реал с total_amount_quote=30, один конфиг.

## [Architect] MindDockOS Cell 3 — нужно обновить — 2026-06-16
TODO (не срочно, в процессе работы):
Добавить новые блоки в Knowledge Base:
- pepe-ab-test2 (testnet бот, 2 контроллера)
- PostgreSQL controller_performance_snapshots (живые данные 13 дней)
- PEPE-test-wide-v8 / PEPE-test-narrow-v1 (A/B тест конфиги)
- binance_perpetual_testnet (новый подключённый коннектор)

Цель: cmd("status") показывает реальные данные из Postgres,
а не хардкод. Интеграция Cell 8 → PostgreSQL.

## [Risk] ИСПРАВЛЕНИЕ ДИАГНОЗА: EARLY_STOP — норма — 2026-06-16
Источник: Gemini (session_monitor агент)

EARLY_STOP в pmm_dynamic = штатный механизм переставления ордеров.
Код 452 = контроллер остановил executor чтобы выставить новый по актуальной цене.
НЕ является проблемой. НЕ требует "лечения".

НОВЫЙ ВОПРОС: почему REALIZED PnL = $0 при 183 EARLY_STOP и volume $25?
Гипотезы:
1. Spreads 0.83/1.48 слишком широкие → ордера не филятся до refresh
2. testnet — нет реального стакана → fills не происходят
3. Нужно смотреть fill rate, а не EARLY_STOP count

СЛЕДУЮЩАЯ ЗАДАЧА [Quant]:
Найти метрику fill rate в логах/snapshots.
Если fills=0 при любых параметрах на testnet → testnet непригоден
для тестирования fill-чувствительных стратегий типа PMM.

## [Instructor] NotebookLM — справочник по Hummingbot — 2026-06-16
Инструмент: NotebookLM (Google)
Содержимое: документация + видеоуроки разработчиков Hummingbot V2
Использование: технические вопросы по механизмам контроллеров,
executor'ов, close types, backtesting engine

Подтверждённый факт из NotebookLM:
EARLY_STOP (код 452) = штатный механизм pmm_dynamic.
Это переставление ордеров по MACD/NATR, а НЕ ошибка.
Большое количество EARLY_STOP = бот активно адаптируется к рынку.

Новый диагноз проблемы убытков:
НЕ "слишком много EARLY_STOP" →
А "ордера не филятся до EARLY_STOP" → REALIZED всегда $0
Это принципиально разные проблемы с разными решениями.

TODO: спросить NotebookLM про fill rate метрики и
оптимальное соотношение executor_refresh_time vs spread width
для получения fills до переставления ордеров.

## [DevOps] Dashboard :8501 — способ остановки инстансов — 2026-06-16
URL: http://localhost:8501/instances
Показывает: все инстансы, NET PNL, Unrealized, Volume, Active Controllers
Кнопка Stop — работает надёжнее чем API /stop-instance (который даёт 404)

Текущее состояние (07:41 UTC):
pepe-ab-test3-20260616-043124 — Running
- PEPE-test-wide-v8: 1000PEPE-USDC, testnet
- PEPE-test-narrow-v1: 1000PEPE-USDT, testnet
NET PNL: -$0.17, Volume: $199.99, возраст 9m
REALIZED=$0 — fills ещё не было на новом инстансе

Следующая проверка через 6-12ч:
Ожидаем первые fills на wide-v8 (spreads 0.002/0.004, refresh 120с)

## [Architect] Итог длинной сессии 2026-06-16 — честная оценка
РЕАЛЬНО СДЕЛАНО (1 результат):
✅ binance_perpetual_testnet подключён к master_account

ОСТАЛЬНОЕ — обучение AI в процессе работы:
- Найдены и исправлены ошибки конфигов (spreads 0.83 → 0.002)
- Понят механизм EARLY_STOP (норма, не проблема)
- Найден правильный путь деплоя через API
- Найден способ остановки: docker stop > API > Dashboard :8501
- Зафиксированы ложные ходы чтобы не повторять

КЛЮЧЕВОЕ ЗНАНИЕ накоплено в CHANGELOG для следующих сессий.
Система MindDock-OS работает как задумано — знания не теряются.

СЛЕДУЮЩАЯ СЕССИЯ — холодный старт:
cd ~/MindDock-OS && git pull -q && tail -100 CHANGELOG.md

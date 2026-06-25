# SESSION HANDOFF — 2026-06-25
# MindDock-OS · gaussian_mm_oneway · БОТА ЗАПУСТИЛИ ✅

---

## ЧТО ДАТЬ КЛОДУ В ПЕРВОМ СООБЩЕНИИ

Скинь три вещи:
1. `cat ~/MindDock-OS/research_gaussian_mm/SESSION_HANDOFF_2026-06-25.md`
2. Скрин Condor с текущим статусом бота
3. Последние логи: `docker logs <bot_name> --tail 50`

---

## ТЕКУЩИЙ СТАТУС (на 2026-06-25 10:37 UTC)

**БОТ РАБОТАЕТ:** `gaussian_mm_oneway` на `binance_perpetual_testnet`
- Пара: 1000PEPE-USDT
- Статус: Running
- Volume: $375
- Total PnL: -$0.10 (unrealized, позиция открыта)
- Realized: $0.00
- CloseType.FAILED: 4, EARLY_STOP: 2

**Контейнер:** `pepe-oneway-v2-20260625-072450` (или следующий)

---

## РАСПОЛОЖЕНИЕ ФАЙЛОВ

```
~/hummingbot-api/bots/
  controllers/market_making/
    gaussian_mm.py              ← базовый (не трогаем)
    gaussian_mm_oneway.py       ← ТЕКУЩИЙ рабочий контроллер
  conf/controllers/
    gaussian_mm_oneway_pepe.yml ← конфиг бота (ТЕКУЩИЙ)

~/MindDock-OS/research_gaussian_mm/
  strategies/
    gaussian_mm_oneway.py       ← источник истины (копируем в hummingbot)
    gaussian_mm_imbalance.py    ← с imbalance filter (следующий шаг)
    gaussian_buffer.py
    skew_shapes_experiment.py
  engine.py                     ← bookDepth-aware matching engine
  single_window/                ← pipeline бэктеста
    config.py, metrics.py, slice_manager.py, visualizer.py
  data_raw/
    1000PEPEUSDT-aggTrades-2026-06-18.csv
    1000PEPEUSDT-bookDepth-2026-06-18.csv
  DEPLOY_PROCEDURE.md           ← процедура деплоя (читать перед деплоем!)
  SESSION_HANDOFF_2026-06-24.md ← предыдущий handoff
  SESSION_HANDOFF_2026-06-25.md ← этот файл
```

---

## ПРОЦЕДУРА ДЕПЛОЯ (кратко)

```bash
# 1. Обновить контроллер
cp ~/MindDock-OS/research_gaussian_mm/strategies/gaussian_mm_oneway.py \
   ~/hummingbot-api/bots/controllers/market_making/gaussian_mm_oneway.py

# 2. Деплой
curl -s -X POST http://localhost:8000/bot-orchestration/deploy-v2-controllers \
  -H "Content-Type: application/json" -u "admin:admin" \
  -d '{"instance_name":"pepe-oneway-v3","credentials_profile":"master_account",
       "controllers_config":["gaussian_mm_oneway_pepe"],
       "image":"hummingbot/hummingbot:latest","headless":true}' | python3 -m json.tool

# 3. Проверить логи
docker logs <unique_instance_name> --tail 30
```

**КРИТИЧНО:** yaml конфиг ОБЯЗАТЕЛЬНО содержит `id: gaussian_mm_oneway_pepe`

---

## ТЕКУЩИЙ КОНФИГ БОТА

```yaml
controller_name: gaussian_mm_oneway
id: gaussian_mm_oneway_pepe
trading_pair: 1000PEPE-USDT
connector_name: binance_perpetual_testnet
candles_connector: binance_perpetual
candles_trading_pair: 1000PEPE-USDT
interval: 1m
total_amount_quote: 500
leverage: 20

# Gaussian
gauss_length: 19
gaussian_layers: 5
natr_length: 4
atr_length: 24
min_natr: 0.0008       # исправлено (было 0.002 — выше рынка)
max_natr: 0.05

# Спреды
buy_spreads: [0.002, 0.003]
sell_spreads: [0.002, 0.003]
buy_amounts_pct: [0.5, 0.5]
sell_amounts_pct: [0.5, 0.5]

# Oneway
trend_threshold: 0.3   # |trend_strength| > 0.3 → одна сторона
price_shift_mult: 0.978
max_shift_pct: 0.003
inventory_skew_mult: 0.5
trend_skew_mult: 0.5

# Риск
stop_loss: 0.015
take_profit: 0.006
time_limit: 7200
trailing_stop:
  activation_price: 0.005
  trailing_delta: 0.002
```

---

## ЧТО БЫЛО СДЕЛАНО ЗА ДВЕ СЕССИИ

### Исследование (single_window_manual.ipynb)
- Построен GaussianSignalEngine (потиковое обновление свечей)
- Найден баг: inventory skew сдвигал reference целиком → ask < bid
- Найден баг: min_natr=0.002 > реального рынка (0.07-0.17%) 100% времени
- Анализ bookDepth imbalance: bid-heavy → цена вниз (контринтуитивно)
- Tested: Baseline, IMB filter, V3 directional, V4 hedge
- Лучший результат: V3+IMB → +0.693 USDT за день (fee=0%, 1 день данных)

### Контроллеры
- `gaussian_mm_oneway.py` — directional MM (написан, протестирован, задеплоен)
  - `position_mode: ONEWAY` — дефолт в Config
  - `open_order_type: LIMIT_MAKER` — maker rebate +0.01%
  - При |trend_strength| > 0.3: одна сторона выключается

### Технические находки
- Binance Perpetual дефолт = HEDGE mode → -2022 ReduceOnly error
- `id` обязателен в yaml (pydantic V2)
- `open_order_type` в yaml = ошибка (Extra inputs not permitted)
- Maker fee на 1000PEPE = 0%, rebate = +0.01%
- API авторизация: `curl -u admin:admin http://localhost:8000/...`

---

## СЛЕДУЮЩИЕ ПРИОРИТЕТЫ

### 1. Анализ данных текущего бота [HIGH]
После остановки бота:
```bash
# Найти SQLite с executors
find ~/hummingbot-api -name "*.sqlite" | head -5
# Или скачать aggTrades за период работы
```
Загрузить в single_window движок, сравнить симуляцию vs реал.

### 2. Доработка движка [HIGH]
```python
# Добавить maker rebate
maker_rebate = config.get("maker_rebate", 0.0001)
total_rebate += fill_price * fill_qty * maker_rebate

# Adaptive order age через NATR
def adaptive_order_age(natr, config):
    ratio = (natr - min_natr) / (max_natr - min_natr)
    return int(max_age - ratio * (max_age - min_age))
```

### 3. gaussian_mm_imbalance.py [MEDIUM]
Уже написан в strategies/. Нужно:
- Добавить `id` в yaml
- Проверить на testnet
- Сравнить с oneway

### 4. Данные других дней [MEDIUM]
Проверить imbalance сигнал на 2026-06-17 и 2026-06-19.
Функция: `analyze_imbalance_day(trades_path, depth_path)`

---

## ИНФРАСТРУКТУРА

```
Docker containers (все Running):
  hummingbot-api:     http://localhost:8000  (Basic Auth: admin:admin)
  dashboard (Condor): http://localhost:8088  (Telegram token auth)
  hummingbot-broker:  emqx:5, port 18083
  hummingbot-postgres: port 5432
  quants-lab:         Jupyter http://localhost:8888

MacBook Pro 2014, i7, 16GB RAM
RAM usage: ~3.5GB, CPU: ~22%
```

---

## КЛЮЧЕВЫЕ КОМАНДЫ

```bash
# Статус ботов
curl -s -u admin:admin http://localhost:8000/bot-orchestration/status | python3 -m json.tool

# Логи бота
docker logs <bot_name> --tail 50

# Остановить и архивировать
curl -s -X POST http://localhost:8000/bot-orchestration/stop-and-archive-bot/<bot_name> \
  -u "admin:admin" | python3 -m json.tool

# Git sync
cd ~/MindDock-OS && git pull -q && git status

# Jupyter
http://localhost:8888/lab/tree/research_notebooks/data_collection/single_window_manual.ipynb
```

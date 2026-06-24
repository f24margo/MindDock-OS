# SESSION HANDOFF — 2026-06-24
# MindDock-OS · research_gaussian_mm · Gaussian MM бэктест

---

## ПРОТОКОЛ СТАРТА СЛЕДУЮЩЕЙ СЕССИИ

```bash
cd ~/MindDock-OS && git pull -q && tail -80 CHANGELOG.md
```
Открыть: `research_notebooks/data_collection/single_window_manual.ipynb`
Запустить ячейки 1–5 для восстановления контекста (engine, данные, warmup).
Затем продолжить с ПРИОРИТЕТ 1 ниже.

---

## СТРАТЕГИЧЕСКИЙ КОНТЕКСТ

**Цель проекта:** Gaussian MM бот для 1000PEPE-USDT на Binance Perpetual.
Подход: запускаем бота на короткое время → получаем реальные данные →
разбираем на стенде (single_window симуляция) → оптимизируем конфиг → повтор.

**Торговые сессии для исследования паттернов:**
- Азия:    00:00–08:00 UTC
- Европа:  08:00–16:00 UTC  
- Нью-Йорк: 16:00–00:00 UTC
- Цель: разные конфиги под разные сессии + недельный диапазон как контекст

---

## ТЕКУЩЕЕ СОСТОЯНИЕ КОДА

### research_gaussian_mm/ (ветка media)
```
engine.py              ← bookDepth-aware matching, PnL способ A
strategies/gaussian_mm.py  ← ЗАГЛУШКА (fixed spread + inv skew)
single_window/
  config.py            ← MM_ENGINE_CONFIG, calculate_lot_size()
  metrics.py           ← run_window_backtest_and_metrics()
  slice_manager.py     ← slice_window(), calculate_max_order_age()
  visualizer.py        ← plot_window_diagnostics()
  sensitivity_analysis.py
data_raw/
  1000PEPEUSDT-aggTrades-2026-06-18.csv
  1000PEPEUSDT-bookDepth-2026-06-18.csv
```

### GaussianSignalEngine (написан в сессии, НЕ сохранён в файл)
- Класс реализован в ячейке Jupyter
- `_compute_signal(candles)` → возвращает (gauss_center, natr, trend_strength, atr)
- `_update_candle(timestamp, price, qty)` → накапливает 1m свечи из тиков
- `get_orders(price, config, position)` → bid/ask с gaussian + inv skew
- **ПРОБЛЕМА:** движок не вызывает `_update_candle()` — свечи не обновляются потиково

---

## РАБОЧАЯ КОНФИГУРАЦИЯ БОТА (yaml)

```yaml
atr_length: 24
gauss_length: 19
gaussian_layers: 5
natr_length: 4
interval: 1m
gauss_distance_base: 1.594
flat_enter: 0.3
flat_exit: 0.59
min_natr: 0.002        # ПРОБЛЕМА: выше реального NATR рынка (0.07-0.17%)
max_natr: 0.05
price_shift_mult: 0.978
max_shift_pct: 0.0015
trend_skew_mult: 0.002  # слишком мал для компенсации тренда
inventory_skew_mult: 0.002
buy_spreads: [0.0015, 0.0015]
sell_spreads: [0.0015, 0.0015]
leverage: 20
total_amount_quote: 100
trading_pair: 1000PEPE-USDT
connector_name: binance_perpetual_testnet
stop_loss: 0.01
take_profit: 0.005
time_limit: 300
trailing_stop:
  activation_price: 0.004
  trailing_delta: 0.002
cooldown_time: 15
executor_refresh_time: 60
```

---

## НАЙДЕННЫЕ ПРОБЛЕМЫ (в порядке важности)

### 1. min_natr > реального рынка (КРИТИЧНО)
- Реальный NATR 1000PEPE 2026-06-18: 0.07–0.17%
- min_natr в конфиге: 0.20%
- Следствие: spread заблокирован выше рыночного движения 100% времени
- Ордера филлятся только когда цена идёт против позиции → убыток

### 2. Inventory skew сдвигает reference целиком вниз (ИСПРАВЛЕН в сессии)
- Старая формула: reference = price * (1 - skew) → ask < bid при больших позициях
- Фикс v2: inv_shift clamp до 2*base_spread
- Фикс v3: asymmetric spread adjustment (bid wider, ask tighter при long)

### 3. Gaussian сигнал не подключён к движку симуляции
- strategies/gaussian_mm.py — ЗАГЛУШКА без gaussian логики
- GaussianMMController (Hummingbot) использует pandas_ta, не портирован
- pandas_ta недоступен в quants-lab окружении (ModuleNotFoundError)

### 4. Движок не обновляет свечи потиково
- GaussianSignalEngine._update_candle() написан но не вызывается
- run_simulation() не передаёт timestamp в get_signals_func
- Сигнал считается по warmup свечам, не обновляется в реальном времени

---

## РЕЗУЛЬТАТЫ БЭКТЕСТА (2026-06-18, spread=0.002, max_pos=3 лота)

| Окно        | Тренд   | Trades | Total PnL | Final Lots | Valid |
|-------------|---------|--------|-----------|------------|-------|
| 00:00-04:00 | ↓1.47%  | 37     | -0.191    | +0.34      | ✅    |
| 04:00-08:00 | ↓0.12%  | 12     | +0.168    | +0.07      | ✅    |
| 08:00-12:00 | ↓0.89%  | 32     | +0.151    | +2.66      | ❌    |
| 12:00-16:00 | ↓3.43%  | 56     | -0.449    | +2.09      | ❌    |
| 16:00-20:00 | ↑1.97%  | 56     | -0.054    | -2.30      | ❌    |
| 20:00-00:00 | ↑0.67%  | 28     | +0.258    | -1.86      | ❌    |
| **TOTAL**   |         | 221    | **-0.117**|            | 2/6   |

**Вывод:** бот прибылен только в боковике (тренд < 0.12%).
При тренде > 0.5% накапливает позицию против направления.

---

## BOOK IMBALANCE АНАЛИЗ

**Данные:** bid/ask depth на уровнях ±0.20%, ±1%, ±2%, ±3%, ±4%, ±5%
**Формула:** imbalance = bid_-0.20 / (bid_-0.20 + ask_0.20)

| Метрика | Значение |
|---------|----------|
| Mean    | 0.522    |
| Std     | 0.056    |
| Min     | 0.222    |
| Max     | 0.708    |
| Corr → fwd_1m  | -0.027 |
| Corr → fwd_15m | -0.084 |

**Ключевой вывод:** корреляция ОТРИЦАТЕЛЬНАЯ.
bid-heavy стакан (imb > 0.55) → цена идёт ВНИЗ.
Интерпретация: bid wall = сопротивление, участники продают агрессивнее.

| Зона imbalance | Среднее движение | Сигнал |
|----------------|-----------------|--------|
| < 0.35         | -0.024%         | ↓ SELL |
| 0.35–0.45      | -0.007%         | ↓ SELL |
| 0.45–0.55      | +0.003%         | → FLAT |
| 0.55–0.65      | -0.013%         | ↓ SELL |
| > 0.65         | -0.056%         | ↓ SELL |

**ВАЖНО:** проверить на других днях перед использованием как торговый сигнал.

---

## ВИЗУАЛИЗАЦИЯ (live_bot_full.html)

Реализована расширенная визуализация коридора bid/ask:
- Mid Price (серый) + MM Bid (зелёный пунктир) + MM Ask (красный пунктир)
- Точки fill: ▲ bid fill, ▼ ask fill
- Вертикальные линии requote + число тиков между ними (прокси плотности)
- Монолитный HTML с base64 PNG (без блокировок браузера)
- Код: в ячейке Jupyter (НЕ сохранён в файл)

**Наблюдение на графике:** после каждого bid fill → зелёный коридор
уходит резко вниз (inventory skew давит reference). Коридор расширяется
против тренда вместо того чтобы помогать закрыть позицию.

---

## ПРИОРИТЕТЫ СЛЕДУЮЩЕЙ СЕССИИ

### ПРИОРИТЕТ 1: Imbalance filter в get_orders [Quant · 1-2ч]
```python
# Логика:
# imb > 0.55 → не покупать (bid = 0)
# imb < 0.45 → не продавать (ask = price * 10)
# Нужно передавать book_row в get_signals_func
```
**Проблема:** engine.py передаёт в get_signals_func только (price, config, position).
Нужно либо:
- а) Добавить book_row как 4й аргумент (изменить сигнатуру engine)
- б) Передавать imbalance через config (обновлять перед каждым вызовом)
- в) Сделать stateful объект который сам читает book_row (предпочтительно)

### ПРИОРИТЕТ 2: Потиковое обновление свечей [Quant · 1ч]
```python
# В run_simulation перед get_signals_func:
engine_obj._update_candle(row["timestamp"], price, qty)
bid, ask, bs, as_ = engine_obj.get_orders(price, config, position)
```
Проблема: нужно передавать engine_obj в run_simulation.
Решение: сделать get_orders методом объекта (уже сделано ✅),
передавать engine_obj.get_orders как get_signals_func.

### ПРИОРИТЕТ 3: Проверка imbalance на других днях [Quant · 30мин]
Скачать данные за 2026-06-17 и 2026-06-19, прогнать тот же анализ.
Нужна функция `analyze_imbalance_day(trades_path, depth_path)`.

### ПРИОРИТЕТ 4: Сохранить unsaved файлы [DevOps · 15мин]
```bash
# В терминале VSCode:
cat ~/MindDock-OS/research_gaussian_mm/strategies/gaussian_buffer.py
cat ~/MindDock-OS/research_gaussian_mm/strategies/skew_shapes_experime*.py
```
Прочитать содержимое, зафиксировать в CHANGELOG что там.

---

## АРХИТЕКТУРНОЕ РЕШЕНИЕ (принято в сессии)

**Подход к исследованию:**
1. Запускаем бота на реале/testnet короткое время
2. Получаем реальные aggTrades + bookDepth данные
3. Загружаем в single_window симуляцию
4. Разбираем поведение через визуализацию коридора
5. Оптимизируем параметры на стенде
6. Деплоим обновлённый конфиг

**Сессионный подход к параметрам:**
- Азия (00:00-08:00): низкая волатильность, узкие спреды, мягкий inv skew
- Европа (08:00-16:00): средняя волатильность, imbalance filter важен
- Нью-Йорк (16:00-00:00): высокая волатильность, широкие спреды, сильный trend filter

---

## ИНФРАСТРУКТУРА (Docker, все Running)

- mongodb: 27017
- hummingbot-api: 8000 (Running 3/3)
- hummingbot-broker: 18083 (emqx:5)
- hummingbot-postgres: 5432
- dashboard (Condor): 8088
- quants-lab: Jupyter 8888

RAM: 3.42GB / CPU: 22% / Disk: 6.9GB free

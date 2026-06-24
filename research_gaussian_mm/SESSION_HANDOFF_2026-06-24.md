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
- Азия:     00:00–08:00 UTC
- Европа:   08:00–16:00 UTC
- Нью-Йорк: 16:00–00:00 UTC
- Цель: разные конфиги под разные сессии + недельный диапазон как контекст

---

## ТЕКУЩЕЕ СОСТОЯНИЕ КОДА

### research_gaussian_mm/ (ветка media)
- engine.py: bookDepth-aware matching, PnL способ A
- strategies/gaussian_mm.py: ЗАГЛУШКА (fixed spread + inv skew)
- single_window/: config.py, metrics.py, slice_manager.py, visualizer.py
- data_raw/: aggTrades + bookDepth за 2026-06-18

### GaussianSignalEngine (написан в сессии, НЕ сохранён в файл)
- _compute_signal(candles) → (gauss_center, natr, trend_strength, atr)
- _update_candle(timestamp, price, qty) → накапливает 1m свечи из тиков
- get_orders(price, config, position) → bid/ask с gaussian + inv skew
- ПРОБЛЕМА: движок не вызывает _update_candle() — свечи не обновляются потиково

---

## РАБОЧАЯ КОНФИГУРАЦИЯ БОТА

atr_length: 24, gauss_length: 19, gaussian_layers: 5, natr_length: 4
gauss_distance_base: 1.594, flat_enter: 0.3, flat_exit: 0.59
min_natr: 0.002 (ПРОБЛЕМА: выше реального NATR рынка 0.07-0.17%)
max_natr: 0.05, price_shift_mult: 0.978, max_shift_pct: 0.0015
trend_skew_mult: 0.002, inventory_skew_mult: 0.002
buy_spreads: [0.0015, 0.0015], sell_spreads: [0.0015, 0.0015]
leverage: 20, total_amount_quote: 100, trading_pair: 1000PEPE-USDT
stop_loss: 0.01, take_profit: 0.005, time_limit: 300
trailing_stop: activation_price: 0.004, trailing_delta: 0.002

---

## НАЙДЕННЫЕ ПРОБЛЕМЫ

1. min_natr > реального рынка (КРИТИЧНО)
   Реальный NATR: 0.07-0.17%, min_natr в конфиге: 0.20%
   Следствие: spread заблокирован выше рыночного движения 100% времени

2. Inventory skew сдвигал reference целиком вниз (ИСПРАВЛЕН)
   Фикс: inv_shift clamp до 2*base_spread

3. Gaussian сигнал не подключён к движку симуляции
   pandas_ta недоступен в quants-lab окружении

4. Движок не обновляет свечи потиково
   _update_candle() написан но не вызывается из run_simulation

---

## РЕЗУЛЬТАТЫ БЭКТЕСТА (2026-06-18, spread=0.002, max_pos=3 лота)

00:00-04:00  down 1.47%   37 trades   PnL -0.191   +0.34 lots  OK
04:00-08:00  down 0.12%   12 trades   PnL +0.168   +0.07 lots  OK
08:00-12:00  down 0.89%   32 trades   PnL +0.151   +2.66 lots  FAIL
12:00-16:00  down 3.43%   56 trades   PnL -0.449   +2.09 lots  FAIL
16:00-20:00  up   1.97%   56 trades   PnL -0.054   -2.30 lots  FAIL
20:00-00:00  up   0.67%   28 trades   PnL +0.258   -1.86 lots  FAIL
TOTAL                     221 trades  PnL -0.117   2/6 valid

Вывод: бот прибылен только в боковике (тренд < 0.12%).

---

## BOOK IMBALANCE АНАЛИЗ

imbalance = bid_-0.20 / (bid_-0.20 + ask_0.20)
Mean=0.522, Std=0.056, Range=0.22-0.71
Corr(imb → fwd_1m):  -0.027
Corr(imb → fwd_15m): -0.084

Зоны:
< 0.35    → -0.024%  SELL
0.35-0.45 → -0.007%  SELL
0.45-0.55 → +0.003%  FLAT
0.55-0.65 → -0.013%  SELL
> 0.65    → -0.056%  SELL

КЛЮЧЕВОЙ ВЫВОД: bid-heavy стакан → цена идёт ВНИЗ (контринтуитивно).
bid wall = сопротивление. Использовать как фильтр ПРОТИВ покупки.
Проверить на других днях перед использованием как торговый сигнал.

---

## ВИЗУАЛИЗАЦИЯ live_bot_full.html

Реализована: коридор bid/ask + точки fill + requote markers + плотность тиков.
Монолитный HTML с base64 PNG.
Код в ячейке Jupyter (НЕ сохранён в файл — нужно сохранить).
Наблюдение: после bid fill зелёный коридор уходит резко вниз —
inventory skew давит reference против тренда.

---

## ПРИОРИТЕТЫ СЛЕДУЮЩЕЙ СЕССИИ

ПРИОРИТЕТ 1: Imbalance filter в get_orders [Quant, 1-2ч]
  imb > 0.55 → bid = 0 (не покупаем)
  imb < 0.45 → ask = price*10 (не продаём)
  Проблема: engine передаёт только (price, config, position)
  Решение: stateful объект читает book через merged_book по индексу тика

ПРИОРИТЕТ 2: Потиковое обновление свечей [Quant, 1ч]
  Вызывать engine_obj._update_candle(ts, price, qty) перед get_orders
  Передавать engine_obj.get_orders как get_signals_func

ПРИОРИТЕТ 3: Проверка imbalance на других днях [Quant, 30мин]
  Скачать 2026-06-17 и 2026-06-19, прогнать analyze_imbalance_day()

ПРИОРИТЕТ 4: Сохранить unsaved файлы [DevOps, 15мин]
  gaussian_buffer.py и skew_shapes_experime... — unsaved в VSCode
  cat ~/MindDock-OS/research_gaussian_mm/strategies/gaussian_buffer.py

---

## СЕССИОННЫЙ ПОДХОД К ПАРАМЕТРАМ (план)

Азия    (00:00-08:00): низкая волатильность, узкие спреды, мягкий inv skew
Европа  (08:00-16:00): средняя волатильность, imbalance filter критичен
NY      (16:00-00:00): высокая волатильность, широкие спреды, trend filter

---

## ИНФРАСТРУКТУРА

Docker (все Running):
  mongodb:5432, hummingbot-api:8000, hummingbot-broker:18083
  hummingbot-postgres:5432, dashboard(Condor):8088, quants-lab:8888
RAM: 3.42GB, CPU: 22%, Disk: 6.9GB free

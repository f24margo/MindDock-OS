# Gaussian Market Making Simulator — Спецификация проекта

```
MindDock-OS/
└── research_gaussian_mm/
    ├── README.md                 # Этот файл — спецификация, статус, план
    ├── market_engine.py          # Векторизованный движок генерации кэша (SciPy/Windows)
    ├── order_matcher_sim.py      # Симулятор ордеров с Elastic Spread
    ├── visualizer.py             # Визуальная сверка ядра против сырой цены
    └── cache/market_cache.npz    # Предрасчитанный кэш (close, gauss_center, natr, ...)
```

## 1. Цель проекта

Стандартный побарный бэктестер (вход/выход по close свечи) непригоден для GaussianMM, потому что стратегия — маркет-мейкер с динамическим объёмом и инвентарным перекосом (`composite_skew`). Побарный тест убивает саму логику, которую мы тестируем: исполнение происходит внутри бара, а не на его закрытии, и объём ордера на каждом уровне зависит от текущего инвентаря в реальном времени.

Решение — гибридный симулятор: векторизованный расчёт индикаторов на всей истории сразу (NumPy/SciPy) + посекундный событийный цикл матчинга ордеров, который пошагово ведёт инвентарь и проверяет исполнение по `high`/`low` каждой секунды.

## 2. Архитектура (5 слоёв)

```
Layer 1: Data Ingestion       → секундные OHLCV (CSV) → df_raw
Layer 2: Market Engine        → Gaussian convolution + NATR → market_cache.npz
Layer 3: MM Engine            → composite_skew, динамические bid/ask уровни
Layer 4: Exchange Engine      → посекундный матчинг ордеров по high/low, инвентарь
Layer 5: Triple Barrier       → TP/SL/timeout для каждой позиции [НЕ РЕАЛИЗОВАНО]
Layer 6: Analytics            → equity curve, inventory heatmap [ЧАСТИЧНО]
```

Текущая реализация (`market_engine.py` + `order_matcher_sim.py`) покрывает Layer 1-4 в упрощённом виде. Layer 5 (Triple Barrier) отсутствует полностью — позиции сейчас не закрываются по TP/SL/времени, только за счёт встречных ордеров и инвентарного сжатия.

## 3. Математика

### 3.1 Gaussian Center (Layer 2)
5 слоёв кумулятивной свёртки `scipy.signal.windows.gaussian`, каждый следующий слой сглаживает выход предыдущего:

```
sigma_i = gauss_base + i * 60,  i = 0..4
kernel_i = gaussian_window(6 * sigma_i, std=sigma_i), normalized
layer_0 = convolve(close, kernel_0, mode='same')
layer_i = convolve(layer_{i-1}, kernel_i, mode='same')
gauss_center = mean(layer_0, ..., layer_4)
```

### 3.2 Волатильность (NATR)
```
TR[t] = max(high[t]-low[t], |high[t]-close[t-1]|, |low[t]-close[t-1]|)
ATR = rolling_mean(TR, natr_length)
NATR = ATR / close * 100
```

### 3.3 Inventory Ratio
```
inventory_ratio = (position * close) / total_quote
```

### 3.4 Elastic Spread (текущая реализация в order_matcher_sim.py)
```
base_spread = (NATR / 100) * GAUSS_DISTANCE_BASE

если position > 0 (long):
    bid_modifier = 1 + position * SPREAD_ELASTICITY   (bid отдаляется, не доливаем лонг)
    ask_modifier = max(0.5, 1 - position * SPREAD_ELASTICITY)  (ask поджимается, легче выйти)
если position <= 0:
    ask_modifier = 1 + max(0, -position * SPREAD_ELASTICITY)
    bid_modifier = 1 - min(0.5, -position * SPREAD_ELASTICITY)

bid = gauss_center * (1 - base_spread * bid_modifier)
ask = gauss_center * (1 + base_spread * ask_modifier)
```

## 4. Статус реализации

### ✅ Подтверждено работает
- Layer 1 (загрузка CSV, 172,801 секундных баров)
- Layer 2 (Gaussian convolution, NATR) — математика верна, но см. Known Issue #1
- Layer 4 упрощённый (матчинг bid/ask против high/low, инвентарь считается верно)
- Elastic spread даёт наблюдаемый эффект сжатия инвентаря (см. историю экспериментов ниже)

### ⚠️ Known Issues (не исправлено)

**Issue #1 — Warmup artifact (КРИТИЧНО)**
`WARMUP_PERIOD = 3600` в `order_matcher_sim.py` недостаточен. Визуальная проверка (`visualizer.py`, см. графики сессии 2026-06-18) показывает, что `gauss_center` сходится к реальной цене только к ~7500-8000 секунде — отклонение в начале периода доходит до +5.5%, и эта область была частично включена в текущий бэктест.
Последствие: все метрики в разделе "Финальные результаты" ниже посчитаны частично на искажённых данных.
`visualizer.py` использует `start_idx = 4000` — граница подобрана на глаз по графику, не формулой. Нужно либо рассчитывать warmup адаптивно (например, по точке где `|price - gauss_center| / price` падает ниже порога на N последовательных баров), либо просто поднять фиксированный warmup до проверенного значения и задокументировать его как константу.

**Issue #2 — Несвязанный масштаб lot_size**
`lot_size = 1.0` — это 1 единица PEPE (не USDT, не % капитала). При цене ~0.000003 это около $0.000003 за лот. Все PnL и inventory в текущих метриках (-3580 PEPE, +0.000509 PnL) не имеют отношения к реальному `total_amount_quote` бота. Грид-серч по параметрам (gamma, flat_enter/exit) в исторических прогонах тоже не сопоставим с реальной экономикой.
Решение: `lot_size` должен вычисляться от `total_amount_quote / N_levels`, как в реальном конфиге `pmm_dynamic`/`gaussian_mm`.

**Issue #3 — Отсутствует Triple Barrier**
Сейчас позиция не закрывается по TP/SL/timeout — закрытие происходит только за счёт встречного ордера. Это не отражает поведение реального бота с `triple_barrier_config`. Без этого слоя нельзя сравнивать симулятор с реальными результатами ботов (см. `knowledge/trailing_stop_optimization.md`).

### ❌ Не реализовано
- Triple Barrier Engine (TP/SL/timeout)
- Inventory Skew Heatmap, Gaussian Center vs Adaptive Center Deviation, Composite Skew Efficiency (аналитические стенды из исходной спецификации)
- Интерактивный плеер (ipywidgets/Plotly FigureWidget) — пока только статичный `visualizer.py`
- Event-driven движок (сейчас обычный `for i in range(...)` посекундный цикл, не событийный)
- Субсекундная модель траектории (Open→Low→High→Close в зависимости от тренда) — сейчас матчинг проверяет high/low независимо, что даёт оптимистичные двойные исполнения внутри одной секунды

## 5. История экспериментов (на данных с Issue #1 и #2, требует пересчёта)

| Версия | Изменение | Сделок | Inventory | Realized PnL |
|---|---|---|---|---|
| Базовая | симметричный спред 0.1% | 126,078 | -14,116 | 0.000944 |
| + NATR-спред | динамический полуспред от волатильности | 93,907 | -12,931 | 0.000403 |
| + Inventory Skew | защитный сдвиг от позиции | 59,972 | -46 | -0.000046 |
| + Flat/Trend filter | сужение/расширение спреда по фазе | 69,573 | -57 | -0.000059 |
| + Trend Shift | проактивный сдвиг за импульсом | 68,447 | -61 | -0.000046 |
| + Elastic Spread | асимметричное расширение от стороны риска | 88,362 | -3,580 | +0.000259 |

**Наблюдение, которое стоит перепроверить после исправления Issues #1-2:** Inventory Skew (строка 3) дал самый резкий эффект на контроль инвентаря (-14116 → -46), но самый низкий/отрицательный PnL. Elastic Spread дал лучший PnL но при этом инвентарь снова разъехался до -3580. Это может означать реальный trade-off между контролем риска и доходностью — или может быть артефактом warmup/масштаба. Нужно пересчитать на чистых данных, чтобы знать, что из этого правда.

## 6. План дальнейшей реализации (по приоритету)

1. **Исправить Issue #1 (warmup)** — поднять `WARMUP_PERIOD` до проверенного значения по графику, либо реализовать адаптивный критерий схождения. Перепроверить визуально через `visualizer.py`.
2. **Исправить Issue #2 (масштаб)** — привязать `lot_size` к `total_amount_quote`, пересчитать всю таблицу из раздела 5 на честных данных.
3. **Добавить Triple Barrier Engine (Layer 5)** — TP/SL/timeout как отдельный модуль, применимый к любой стратегии, не только GaussianMM.
4. **Пересчитать грид-серч** параметров (gamma, flat_enter, flat_exit) на исправленных данных — текущий топ-5 в истории неинформативен.
5. **Event-driven рефакторинг** — заменить `for i in range(seconds)` на обработку только точек изменения состояния, для ускорения прогонов при оптимизации.
6. **Аналитический дашборд** — inventory heatmap, equity curve (realized vs unrealized раздельно), composite skew efficiency.
7. **Интерактивный плеер** — ipywidgets + Plotly FigureWidget для покадрового просмотра микроструктуры.

## 7. Запуск компонентов

```bash
cd research_gaussian_mm
python market_engine.py        # генерирует cache/market_cache.npz
python order_matcher_sim.py    # запускает симуляцию и аудит PnL
python visualizer.py           # визуальная сверка ядра против сырой цены
```

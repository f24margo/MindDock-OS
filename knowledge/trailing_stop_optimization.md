# Trailing Stop Optimization · Процедура

## Цель
Максимизировать avg pnl_quote на сделку за счёт правильной настройки
activation_price и trailing_delta.

## Шаг 1 · Собрать данные
**close_type:** 2=SL · 3=TimeLimit · 4=TrailingStop · 5=EarlyStop · 6=TrailingStop

## Шаг 2 · Сравнить TimeLimit vs TrailingStop
**Ключевой вопрос:** avg pnl TimeLimit > avg pnl TrailingStop?
- Если да → trailing_delta слишком широкий, срезает рано → уменьшить delta
- Если нет → trailing работает лучше TimeLimit, можно уменьшить activation

## Шаг 3 · Проверить фактическое движение по TimeLimit сделкам
**Ключевой вопрос:** avg pnl TimeLimit > avg pnl TrailingStop?
- Если да → trailing_delta слишком широкий, срезает рано → уменьшить delta
- Если нет → trailing работает лучше TimeLimit, можно уменьшить activation

## Шаг 3 · Проверить фактическое движение по TimeLimit сделкам
**Формула движения:**
- Buy (side=1): (close_price - entry_price) / entry_price
- Sell (side=2): (entry_price - close_price) / entry_price

**Вопрос:** достигали ли TimeLimit сделки activation_price?
- Если все > activation → проблема в delta, не в activation
- Если часть < activation → уменьшить activation_price

## Шаг 4 · Принять решение

| Симптом | Диагноз | Действие |
|---|---|---|
| TrailingStop avg pnl < TimeLimit avg pnl | delta слишком широкий | trailing_delta ↓ |
| TimeLimit сделки не достигают activation | activation слишком высокий | activation_price ↓ |
| Много SL, мало Trailing | activation слишком высокий | activation_price ↓ |
| Trailing срабатывает в минус | delta слишком узкий + шум | trailing_delta ↑ или activation ↑ |

## Шаг 5 · Применить изменение (on-the-fly)
**Формула движения:**
- Buy (side=1): (close_price - entry_price) / entry_price
- Sell (side=2): (entry_price - close_price) / entry_price

**Вопрос:** достигали ли TimeLimit сделки activation_price?
- Если все > activation → проблема в delta, не в activation
- Если часть < activation → уменьшить activation_price

## Шаг 4 · Принять решение

| Симптом | Диагноз | Действие |
|---|---|---|
| TrailingStop avg pnl < TimeLimit avg pnl | delta слишком широкий | trailing_delta ↓ |
| TimeLimit сделки не достигают activation | activation слишком высокий | activation_price ↓ |
| Много SL, мало Trailing | activation слишком высокий | activation_price ↓ |
| Trailing срабатывает в минус | delta слишком узкий + шум | trailing_delta ↑ или activation ↑ |

## Шаг 5 · Применить изменение (on-the-fly)
Бот подхватывает через ~60 секунд. Перезапуск не нужен.

## Шаг 6 · Оценить результат
Подождать минимум 1 сессию (8ч). Затем повторить Шаг 1-2 и сравнить:
- avg pnl TrailingStop до vs после
- доля TrailingStop vs TimeLimit в общем объёме закрытий

## История изменений PEPE-test-wide-v8
| Дата | Параметр | До | После | Причина |
|---|---|---|---|---|
| 2026-06-17 | trailing_delta | 0.003 | 0.001 | TrailingStop avg +0.28% vs TimeLimit +0.76% |

## Правило
Один параметр за раз. Минимум 1 сессия между изменениями.
Фиксировать каждое изменение в TRADING_LOG.md.

---

## Эталонный конфиг для проверки — PEPE-dynamic_PEPE_real_USDC

### Результаты (реальный Binance, 6-8 июня 2026)
- Общий PnL: +1.57 / +1.68 USDT за сутки
- Asia:   -0.35 (убыточная)
- Europe: +0.45
- USA:    +0.97 (лучшая)
- Night:  +0.66

### Лучшие часы UTC: 07, 13, 15, 17
### Худшие часы UTC: 01, 04, 09, 18

### Конфиг
- connector: binance_perpetual (реал, не testnet)
- trading_pair: 1000PEPE-USDC
- buy/sell_spreads: [0.83, 1.48]
- take_profit: 0.003
- stop_loss: 0.005
- trailing_stop: activation=0.0015, delta=0.0008
- time_limit: 1800 (30 мин)
- total_amount_quote: 100
- leverage: 20
- amounts_pct: [0.3, 0.7]
- macd: fast=5, signal=5, slow=42
- natr_length: 7

### Отличия от текущего wide-v8
- Спреды в 400x шире (0.83% vs 0.002%)
- SL в 10x жёстче (0.005 vs 0.05)
- time_limit в 8x короче (1800 vs 14400)
- Реальный коннектор — нет IP ban артефактов

### Статус
Гипотеза для проверки — не копировать слепо.
Сначала протестировать на testnet с теми же параметрами.

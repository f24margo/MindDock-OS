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

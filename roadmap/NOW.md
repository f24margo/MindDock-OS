# NOW · Приоритеты прямо сейчас
_Обновлять в начале каждой сессии_
_Версия: 2026-08-01_

## Топ-3 активных задачи
1. [Risk/Quant] gaussian_mm_hedge · полноценный прогон после апдейта стека
   Нужно: будний день, NY/Europe сессия, 4-6ч
   Проверить: close_type breakdown (PostgreSQL) относительно состояния до
   апдейта Condor/hummingbot-api/dashboard до 2.16.0
   Известно: maker-сделки прибыльны (+$0.43), taker-выходы убыточны (-$3.42) —
   TIME_LIMIT/STOP_LOSS/TRAILING_STOP всегда taker

2. [Quant] Multi-window research на research_gaussian_mm/
   Ограничение: single-window методология завершена и одобрена
   (tanh baseline +0.084, spread=0.15% +0.624/55 trades, Gaussian ось
   невалидна на trend-окне). Следующий шаг: те же параметры на разных
   4-часовых окнах с иным характером рынка — БЕЗ выводов о параметрах
   до multi-window подтверждения. Код для multi-window ещё не написан.

3. [DevOps] hbot CLI — проверить применимость
   Новый неинтерактивный CLI Hummingbot 2.16.0 (start/stop/status, --json,
   без MQTT). Проверить доступность в контейнере и видит ли он инстансы,
   поднятые через hummingbot-api — потенциал для автоматизации
   session-boundary рестарта (сейчас делается вручную)

## Следующие в очереди
- research_gaussian_mm: увеличить lot_size / total_amount_quote для
  реалистичного $ PnL; разделить maker/taker fee в конфиге
- Портировать pmm_dynamic в engine.py интерфейс для бэктеста на
  реальных aggTrades/bookDepth
- quants-lab: навигатор + чистка дубликатов (объём ~2-3ч отдельной сессии)
- MindDock OS Cell 3: обновить Knowledge Base под текущее состояние

## Активные ограничения (не нарушать)
- Single-window методология: НЕ писать multi-window код без явного
  подтверждения Mykola
- Живая логика gaussian_mm (Gaussian smoothing, NATR/ATR, flat_enter/exit,
  trailing stop) НЕ переносится в backtest без отдельного запроса
- Перед любым деплоем (реал ИЛИ testnet): показать конфиг, спросить
  подтверждение, дождаться явного "да"

## Аварийный протокол
ЗАВИСЛО → docker stop {instance_name}
API не работает → используй Dashboard :8501/instances

## Холодный старт сессии
cd ~/MindDock-OS && git pull -q && cat roadmap/NOW.md && tail -100 CHANGELOG.md

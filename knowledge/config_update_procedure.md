# Изменение конфига бота на лету

## 1. Применить изменение
```
curl -X POST "http://localhost:8000/controllers/configs/PEPE-test-wide-v8" \
-u "admin:admin" \
-H "Content-Type: application/json" \
-d '{"trailing_stop": {"activation_price": 0.006, "trailing_delta": 0.001}}'
```
Заменить значения на нужные. Ждать ~60 секунд.

## 2. Проверить что файл обновился
```
docker exec hummingbot-api cat /hummingbot-api/bots/conf/controllers/PEPE-test-wide-v8.yml
```

## 3. Проверить статус бота
```
curl -s "http://localhost:8000/bot-orchestration/pepe-wide-night-20260616-195815/status" \
-u "admin:admin" | python3 -m json.tool
```
Заменить `pepe-wide-night-20260616-195815` на имя активного бота.

---

## Шаблоны изменений (копировать целиком)

### Trailing stop
```
curl -X POST "http://localhost:8000/controllers/configs/PEPE-test-wide-v8" \
-u "admin:admin" \
-H "Content-Type: application/json" \
-d '{"trailing_stop": {"activation_price": 0.006, "trailing_delta": 0.001}}'
```

### Take profit
```
curl -X POST "http://localhost:8000/controllers/configs/PEPE-test-wide-v8" \
-u "admin:admin" \
-H "Content-Type: application/json" \
-d '{"take_profit": 0.006}'
```

### Spreads
```
curl -X POST "http://localhost:8000/controllers/configs/PEPE-test-wide-v8" \
-u "admin:admin" \
-H "Content-Type: application/json" \
-d '{"buy_spreads": [0.002, 0.004], "sell_spreads": [0.002, 0.004]}'
```

### Stop loss
```
curl -X POST "http://localhost:8000/controllers/configs/PEPE-test-wide-v8" \
-u "admin:admin" \
-H "Content-Type: application/json" \
-d '{"stop_loss": 0.03}'
```

---

## Важно
- Condor UI показывает старый кэш — не верить UI, проверять через Шаг 2
- Нельзя менять на лету: connector_name, trading_pair, leverage
- Binance testnet банит IP при высокой нагрузке — это норма для testnet

## ВАЖНО: Баг API при частичном обновлении
POST /controllers/configs перезаписывает файл ТОЛЬКО переданными полями.
Результат: файл обрезается до 3 строк → бот нельзя деплоить из Editor.

### Правильный порядок при изменении параметра:
1. Скопировать полный конфиг из инстанса:
   cat ~/hummingbot-api/bots/instances/{bot}/conf/controllers/{config}.yml

2. Восстановить полный файл через docker exec с нужным изменением:
   docker exec hummingbot-api sh -c 'cat > /hummingbot-api/bots/conf/controllers/{config}.yml << EOF
   ... полный конфиг ...
   EOF'

3. Проверить в Editor — файл должен быть полным и в правильной папке.

## Проблема: heredoc и Python ломаются при копипасте из чата
Симптом: терминал зависает в `heredoc>` или zsh выдаёт parse error.
Причина: невидимые символы из чата.

Решение: попросить Claude создать .py файл в облаке → скачать → запустить локально.
Пример:
  python3 ~/Desktop/script.py

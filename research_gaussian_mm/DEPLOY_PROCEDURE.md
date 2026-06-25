# ПРОЦЕДУРА ДЕПЛОЯ СТРАТЕГИИ НА HUMMINGBOT API

## РАСПОЛОЖЕНИЕ ФАЙЛОВ

    ~/hummingbot-api/
    bots/controllers/market_making/
        gaussian_mm_oneway.py       - oneway стратегия (ТЕКУЩАЯ)
    bots/conf/controllers/
        gaussian_mm_oneway_pepe.yml - конфиг бота (ТЕКУЩИЙ)

    ~/MindDock-OS/research_gaussian_mm/
    strategies/
        gaussian_mm_imbalance.py    - tanh + imbalance filter
        gaussian_buffer.py          - Gaussian предобработка + lag
        skew_shapes_experiment.py   - 4 формы skew

## ВАЖНО: ОБЯЗАТЕЛЬНОЕ ПОЛЕ В КОНФИГЕ

Конфиг ОБЯЗАТЕЛЬНО содержит поле id (требование pydantic V2):
    id: gaussian_mm_oneway_pepe

Без него контейнер упадёт: validation error for GaussianMMOnewayConfig / id: Field required

## ПРОЦЕДУРА ДЕПЛОЯ

Шаг 1 — обновить файл стратегии (если менялся код):
    cp ~/MindDock-OS/research_gaussian_mm/strategies/gaussian_mm_oneway.py \
       ~/hummingbot-api/bots/controllers/market_making/gaussian_mm_oneway.py

Шаг 2 — проверить конфиг (id обязателен):
    cat ~/hummingbot-api/bots/conf/controllers/gaussian_mm_oneway_pepe.yml

Шаг 3 — остановить старый контейнер:
    docker ps -a | grep pepe
    docker stop <container_name>
    docker rm <container_name>

Шаг 4 — задеплоить:
    curl -s -X POST http://localhost:8000/bot-orchestration/deploy-v2-controllers \
      -H "Content-Type: application/json" \
      -u "admin:admin" \
      -d '{"instance_name":"pepe-oneway-v2","credentials_profile":"master_account","controllers_config":["gaussian_mm_oneway_pepe"],"image":"hummingbot/hummingbot:latest","headless":true}' | python3 -m json.tool

Запомнить unique_instance_name из ответа (pepe-oneway-v2-YYYYMMDD-HHMMSS).

Шаг 5 — проверить статус:
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep pepe
    docker logs <unique_instance_name> 2>&1 | tail -50

Шаг 6 — остановить бота:
    curl -s -X POST http://localhost:8000/bot-orchestration/stop-and-archive-bot/<name> \
      -u "admin:admin" | python3 -m json.tool

## АУТЕНТИФИКАЦИЯ API

HTTP Basic Auth: -u "admin:admin" (из ~/hummingbot-api/.env)
API URL: http://localhost:8000

## ИНФРАСТРУКТУРА

Проверка контейнеров:
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "hummingbot|condor"

Логи в реальном времени:
    docker logs -f <unique_instance_name>

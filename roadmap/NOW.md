# NOW · Приоритеты прямо сейчас
_Обновлять в начале каждой сессии_
_Версия: 2026-06-17_

## Топ-3 активных задачи
1. [strategies/pmm_dynamic] PEPE-test-wide-v8 · наблюдаем trailing_delta=0.001
   Бот работает: pepe-ab-test3-20260616-043124
   Изменено: trailing_delta 0.003→0.001 (2026-06-17)
   Проверка: knowledge/trailing_stop_optimization.md

2. [strategies] Optuna: пересмотр шага спреда (step=0.0001, log=True)
   Статус: гипотеза зафиксирована, не тестирована

3. [research] quants-lab: навигатор + чистка дубликатов
   Статус: план зафиксирован в CHANGELOG.md
   Объём: ~2-3ч отдельной сессии

## Следующие в очереди
- gaussian_mm: возобновить после стабилизации pmm_dynamic
- MindDock OS Cell 3: обновить Knowledge Base под текущее состояние
- roadmap/: наполнить ветки strategies/, infrastructure/, trading/

## Аварийный протокол
ЗАВИСЛО → docker stop {instance_name}
API не работает → используй Dashboard :8501/instances

## Холодный старт сессии
cd ~/MindDock-OS && git pull -q && cat roadmap/NOW.md && tail -50 CHANGELOG.md

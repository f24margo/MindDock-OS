# NOW · Приоритеты прямо сейчас
_Обновлять в начале каждой сессии_
_Версия: 2026-06-16_

## Топ-3 активных задачи
1. [strategies/pmm_dynamic] A/B тест wide vs narrow — наблюдаем результаты
   Боты работают: pepe-ab-test3-20260616-043124
   Проверка: см. CHANGELOG.md → запрос к PostgreSQL

2. [strategies] Optuna: пересмотр шага спреда (step=0.0001, log=True)
   Статус: гипотеза зафиксирована, не тестирована
   Файл: knowledge/ → [Quant]

3. [infrastructure] quants-lab: навигатор + чистка дубликатов
   Статус: план зафиксирован в CHANGELOG.md
   Объём: ~2-3ч отдельной сессии

## Следующие в очереди
- gaussian_mm: возобновить после стабилизации pmm_dynamic
- MindDock OS Cell 3: обновить Knowledge Base под текущее состояние
- _draft_roadmap: наполнить ветки trading/, strategies/, infrastructure/

## Аварийный протокол
ЗАВИСЛО → docker stop {instance_name}
API не работает → используй Dashboard :8501/instances

## Холодный старт сессии
cd ~/MindDock-OS && git pull -q && cat _draft_roadmap/NOW.md && tail -50 CHANGELOG.md

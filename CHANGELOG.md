# CHANGELOG · MindDock-OS
> История проекта. Читать с конца — последнее сверху.
> Формат: [Роль] что произошло

---

## 2026-06-13

### Торговля
- [Analyst] gaussian_mm · Europe убыток · USA +$1.06 · Night +$0.55
- [Analyst] Паттерн подтверждён: Гаусс любит волатильность USA и тихую азию
- [Risk] pmm_dynamic остановлен · gaussian_mm запущен на замену
- [Analyst] session_monitor (Gemini) собирает статистику автоматически ✅

### MindDock OS
- [Architect] MindDock-OS репо создан на GitHub
- [Architect] MindDockOS.ipynb · Cell 1-8 sealed · реактивный цикл работает
- [Architect] render_browser() · карта системы открывается в браузере
- [Architect] Принцип зафиксирован: MindDock не хранит знания — хранит карту
- [Algo-Dev] Help Engine реализован · cmd("help"), cmd("status"), cmd("focus")
- [DevOps] GitHub push · quants-lab · 83 файла · история кода сохранена

## 2026-06-12

### Торговля
- [Analyst] gaussian_mm запущен на реале · 1000PEPE-USDC · leverage=20
- [Risk] pmm_dynamic · 94% EARLY_STOP · time_limit=7200 · проблема зафиксирована
- [Analyst] Варианты A/B/C для fix EARLY_STOP готовы → отложено

### MindDock OS
- [Architect] Концепция MindDock OS сформулирована
- [Architect] Три уровня памяти: PROJECT_CONTEXT · NAVIGATOR · SESSION_LOG
- [Architect] Матрица ролей: Quant · Algo-Dev · DevOps · Risk · Analyst · Instructor · Architect
- [Architect] MISSION: открытая лаборатория · новый участник за 1 день в теме
- [DevOps] Инфраструктура проверена · 7 Docker контейнеров · endpoints задокументированы

---

## Протокол новой сессии
1. Прочитай последние 5 строк CHANGELOG.md
2. Загрузи PROJECT_CONTEXT.md + SESSION_LOG.md
3. Напиши: "Продолжаем. Фокус: [Роль] [задача]"

## Открытые вопросы
- [ ] PostgreSQL :5432 — что хранится?
- [ ] EARLY_STOP fix для gaussian_mm — варианты A/B/C
- [ ] scan_project() — автонаполнение карты
- [ ] minddock_core.py — финальная сборка
- [DevOps] session_stats.py путь: ~/condor/trading_agents/session_monitor/routines/

## 2026-06-14

### База данных — уточнение
- MongoDB ЖИВАЯ: quants_lab → коллекция "experiments" (3-4 записи, EXP_001/optuna)
- Предыдущая проверка через mongosh показала [] — вероятно смотрели через другое подключение/контейнер
- TODO: найти скрипт который пишет в experiments, сверить с mongosh

### Железо — ограничение проекта
- MacBook Pro 11,2 (2014) · Intel i7 2.2GHz · 4 ядра · 16GB RAM
- Docker Desktop 4.20.1 (устаревший)
- Решение: обновлять Condor осторожно, поэтапно, с проверкой нагрузки на каждом шаге

### Condor — точка входа найдена
- Запуск: `cd ~/condor && python3 main.py`
- Использует системный Python 3.12 (НЕ conda env)
- Процесс работает непрерывно 3+ дня без перезапуска
- Порт 8088, PID меняется при каждом запуске

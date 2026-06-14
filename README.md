# MindDock-OS

# MindDock-OS

Контекстная операционная система для quants-lab.
Трейдер-инженер + AI работают в едином контуре: рынок → код → знания → рынок.

---

## Миссия

Открытая лаборатория знаний для создания прибыльных алгостратегий.
Новый участник (человек или AI) понимает систему за 1 день и движется самостоятельно.

---

## Эндпоинты (живая система)

| Сервис | Адрес | Роль |
|---|---|---|
| Condor | http://localhost:8088 | Управление ботами, AI агенты, рутины |
| hummingbot-api | http://localhost:8000 | Исполнение (admin/admin) |
| Dashboard | http://localhost:8501 | Dev-мониторинг (предшественник Condor) |
| MongoDB UI | http://localhost:28081 | Просмотр данных |
| Jupyter Lab | http://localhost:8888 | MindDockOS.ipynb, бэктест |

---

## Карта проекта

| Файл | Что внутри |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | Инженерная история — код, архитектура, решения |
| [TRADING_LOG.md](TRADING_LOG.md) | Финансовая история — PnL, паттерны, выводы |
| [notebooks/MindDockOS.ipynb](notebooks/MindDockOS.ipynb) | Ядро системы — Cell 1-8, реактивный цикл |
| [knowledge/](knowledge/) | Найденные скрипты, пути, рутины Condor |

---

## Матрица ролей AI

```
[Quant]      математика · Optuna · бэктест
[Algo-Dev]   контроллеры · Python · архитектура
[DevOps]     Docker · API · инфраструктура
[Risk]       капитал · стопы · экстренные протоколы
[Analyst]    рынок · post-trade · рекомендации
[Instructor] маршруты · гайды · обучение
[Architect]  проектирование · связи · новое
```

---

## Протокол новой сессии

1. Открой [CHANGELOG.md](CHANGELOG.md) — последние 5 строк, раздел "Текущий фокус" сверху
2. Покажи AI эту страницу или ссылку на репо
3. Напиши: `Продолжаем. Фокус: [Роль] [задача]`

---

## Принцип

> MindDock не хранит знания. MindDock хранит карту знаний.

Знания живут в файлах. Система знает где они и как к ним перейти.

---

*MindDock OS v2.0 · github.com/f24margo/MindDock-OS*



MindDock OS — це модульне робоче середовище трейдера-інженера, побудоване на архітектурі System Bus. Система автоматизує розробку стратегій (зокрема Gaussian MM v7.1), інтегруючи двигун Hummingbot, MongoDB та ШІ-агентів через реактивний інтерфейс у Jupyter Lab

MindDock-OS/
│
├── notebooks/
│   ├── MindDockOS.ipynb
│   └── experiments/
│
├── knowledge/
│   ├── objects/
│   ├── articles/
│   └── templates/
│
├── mongodb/
│
├── docs/
│
├── src/
│
├── assets/
│
└── README.md


/Users/nikolayfilatov/MindDock-OS
ROOT
│
├── docs/
├── notebooks/
├── src/
├── knowledge/
├── assets/
├── scripts/
├── tests/
└── README.md

/Users/nikolayfilatov/MindDock-OS/

├── knowledge/
│   ├── passports/
│   ├── articles/
│   ├── templates/
│   ├── imports/
│   └── exports/

где:

passports/ — шаблоны паспортов объектов (gaussian_mm.json, condor.json);
articles/ — большие статьи и инструкции;
templates/ — стандартные формы заполнения;
imports/ — материалы для массовой загрузки;
exports/ — резервные копии из MongoDB.

PROJECT_ROOT = "/Users/nikolayfilatov/MindDock-OS"
from pathlib import Path

SYSTEM["paths"] = {
    "root": Path("/Users/nikolayfilatov/MindDock-OS"),
    "docs": Path("/Users/nikolayfilatov/MindDock-OS/docs"),
    "knowledge": Path("/Users/nikolayfilatov/MindDock-OS/knowledge"),
    "notebooks": Path("/Users/nikolayfilatov/MindDock-OS/notebooks"),
    "src": Path("/Users/nikolayfilatov/MindDock-OS/src"),
    "assets": Path("/Users/nikolayfilatov/MindDock-OS/assets"),
}
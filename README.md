# MindDock-OS
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
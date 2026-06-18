
## ИСПРАВЛЕНИЕ: Dify слишком тяжёл для MacBook 2014
9-10GB образов — неприемлемо для старого железа.

## Лёгкий вариант: ChromaDB + Jupyter
- ChromaDB: ~200MB (векторная БД)
- sentence-transformers: ~500MB (эмбеддинги без LLM)
- Интерфейс: Jupyter ноутбук :8888 (уже работает)
- Итого: ~700MB vs 9GB у Dify

Скрипт индексирует: ~/MindDock-OS/**/*.md
Поиск: семантический по всей базе знаний

## Hummingbot v2.15.0 — 2026-06-17
- Tailscale: безопасный доступ к API (важно для облака)
- OpenRouter: бесплатные LLM модели для Condor Agent
- Perpetual Connector fixes: управление позициями улучшено
- Обновление: выполнить по UPDATE_PROCEDURE.md в отдельную сессию
- Ссылка: https://hummingbot.org/release-notes/2.15.0/

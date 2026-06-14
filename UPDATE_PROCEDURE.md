# UPDATE PROCEDURE — Condor / зависимости
> Повторяемая процедура обновления. Используется локально и в облаке.

---

## Когда применять
- Обновление Condor (git pull из upstream)
- Обновление Python-зависимостей (uv sync)
- Любое изменение которое может затронуть работающие боты

---

## Ограничения текущей среды (учитывать всегда)

```
Локально:  MacBook Pro 2014, Intel x86_64, macOS 11, 16GB RAM
           -> некоторые пакеты не имеют colес под старый macOS
           -> ARM-only / Linux-only зависимости ломают uv sync

Облако:    планируется (Linux x86_64 или ARM)
           -> большинство пакетов будут доступны
           -> но: повторить процедуру, не пропускать шаги бэкапа
```

---

## Процедура (шаги)

### 1. Остановить торговлю заранее
- Закрыть позиции или дождаться flat
- Остановить ботов в Condor
- Зафиксировать в TRADING_LOG какой бот/конфиг был активен

### 2. Бэкап ПЕРЕД любыми изменениями
```bash
cp -r ~/condor ~/condor_backup_$(date +%Y%m%d)
du -sh ~/condor_backup_$(date +%Y%m%d)
```
Проверить размер — должен быть похож на исходную папку (не 0, не пустой).

### 3. Сохранить локальные изменения
```bash
mkdir -p ~/MindDock-OS/knowledge/condor_local_changes_$(date +%Y%m%d)
git -C ~/condor diff > ~/MindDock-OS/knowledge/condor_local_changes_$(date +%Y%m%d)/diff_before_update.patch
```

### 4. Проверить untracked файлы (НАШИ файлы — не должны потеряться)
```bash
git -C ~/condor status
```
Убедиться что видны:
- routines/session_stats.py
- routines/position_summary.py
- routines/update_bot_config.py
- trading_agents/

### 5. Stash + pull
```bash
git -C ~/condor stash
git -C ~/condor pull origin main
```
Если конфликты при pull — НЕ форсить, разбираться по файлу.

### 6. Проверить что наши файлы целы
```bash
ls ~/condor/routines/ | grep -E "session_stats|position_summary|update_bot_config"
ls ~/condor/trading_agents/
```

### 7. Синхронизация зависимостей
```bash
cd ~/condor && uv sync
```

**Известная проблема (локально, x86_64 macOS):**
```
onnxruntime не имеет колеса под macosx_11_0_x86_64
-> приходит транзитивно через faster-whisper (voice/transcribe, не используется)
-> решение: убрать "faster-whisper" из pyproject.toml зависимостей
```
Если в облаке (Linux) — этот шаг скорее всего не понадобится, faster-whisper может остаться.

### 8. Запуск (ВАЖНО — правильная команда)
```bash
cd ~/condor && uv run python3 main.py
```
НЕ использовать `python3 main.py` напрямую — системный Python не видит venv-зависимости (ModuleNotFoundError: telegram).

### 9. Проверка порта перед запуском (если "address already in use")
```bash
lsof -i :8088
kill <PID>
sleep 2
cd ~/condor && uv run python3 main.py
```

### 10. После старта — проверить
- Логи: "Application startup complete", "Uvicorn running on http://0.0.0.0:8088"
- Открыть localhost:8088, hard refresh (Cmd+Shift+R)
- Проверить hummingbot-api: `curl http://localhost:8000/controllers/ -u admin:admin`
- docker ps — все контейнеры живы

### 11. Зафиксировать результат
- CHANGELOG.md: что изменилось, что было исправлено
- Если были проблемы и решения — записать в knowledge/

---

## Для облака (на будущее)

Дополнительно проверить:
- [ ] Переменные окружения / .env переносятся отдельно (секреты не в git)
- [ ] MongoDB/Postgres данные — бэкап перед миграцией
- [ ] API ключи Binance — IP whitelist на новый IP облака
- [ ] Порты 8088/8000/8501/27017/28081/5432 — доступны только нужным пользователям
- [ ] systemd/supervisor вместо ручного `uv run` — автозапуск после реолада

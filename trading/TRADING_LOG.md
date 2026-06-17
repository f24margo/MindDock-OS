cat > ~/MindDock-OS/TRADING_LOG.md << 'EOF'
# TRADING_LOG · MindDock-OS
> Финансовая история. Только факты и выводы.
> Формат: дата · стратегия · результат · вывод

---

## 2026-06-13

### gaussian_mm · 1000PEPE-USDC · v82
Asia:    +$0.09  ✅  тихий рынок · TRAILING работает

Europe:  -$0.36  ❌  направленное движение · STOP_LOSS x9

USA:     +$1.06  ✅  волатильность · TimeLimit прибыльный

Night:   +$0.55  ✅  азиатская · стабильно

Итог:    +$1.34

**Паттерн:** Гаусс зарабатывает в USA и ночью. Europe убивает.
**Вывод:** рассмотреть отключение в Europe сессию.
**Конфиг:** flat_enter=0.3 · flat_exit=0.59 · layers=5 · interval=1m

---

## 2026-06-12

### gaussian_mm · первый запуск на реале
Старт:   17:00 UTC

Volume:  $476 → $3.5K за день

Итог:    -$0.36
**Проблема:** STOP_LOSS вырос с 3 до 27 за NY/EU сессию.
**Вывод:** стратегия чувствительна к направленным движениям.

### pmm_dynamic · 1000PEPE-USDC
Итог:    -$0.46 за день
**Проблема:** 94% закрытий = EARLY_STOP · time_limit=7200
**Гипотезы A/B/C:** готовы · не тестированы → отложено

---

## Открытые вопросы
- [ ] Отключить gaussian_mm в Europe сессию · проверить результат
- [ ] Протестировать варианты A/B/C для pmm_dynamic
- [ ] Накопить статистику за неделю → принять решение по параметрам

## Шаблон записи (копировать каждый день)
ГГГГ-ММ-ДД
стратегия · пара · версия
Asia:    $X

Europe:  $X

USA:     $X

Night:   $X

Итог:    $X

Паттерн:

Вывод:

Конфиг:
EOF

git add TRADING_LOG.md
git commit -m "[Analyst] TRADING_LOG.md — финансовая история"
git push origin media
# TRADING LOG - MindDock-OS
Historia finansovyh rezul'tatov. Tol'ko fakty i vyvody.

---

## 2026-06-13

### gaussian_mm - 1000PEPE-USDC - v82

Asia:    +$0.09  OK  - tihij rynok, TRAILING rabotaet
Europe:  -$0.36  XX  - napravlennoe dvizhenie, STOP_LOSS x9
USA:     +$1.06  OK  - volatilnost, TimeLimit pribylen
Night:   +$0.55  OK  - aziatskaya, stabilno
Itog:    +$1.34

Pattern: Gauss zarabatyvaet v USA i noch'yu. Europe ubivaet.
Vyvod: rassmotet' otklyuchenie v Europe sessiyu.
Konfig: flat_enter=0.3, flat_exit=0.59, layers=5, interval=1m

---

## 2026-06-12

### gaussian_mm - pervyj zapusk na reale

Start:  17:00 UTC
Volume: $476 - $3.5K za den'
Itog:   -$0.36

Problema: STOP_LOSS vyros s 3 do 27 za NY/EU sessiyu.
Vyvod: strategiya chuvstvitelna k napravlennym dvizheniyam.

### pmm_dynamic - 1000PEPE-USDC

Itog: -$0.46 za den'
Problema: 94% zakrytij = EARLY_STOP, time_limit=7200
Gipotezy A/B/C: gotovy, ne testirovany - otlozheno

---

## Otkrytye voprosy

1. Otklyuchit gaussian_mm v Europe sessiyu - proverit rezultat
2. Protestirovat varianty A/B/C dlya pmm_dynamic
3. Nakopit statistiku za nedelyu - prinyat reshenie po parametram

## Shablon zapisi (kopirovat kazhdyj den')

Data: YYYY-MM-DD
Strategiya:
Asia:
Europe:
USA:
Night:
Itog:
Pattern:
Vyvod:
Konfig:

---
## 2026-06-16
### pmm_dynamic A/B тест · testnet · pepe-ab-test3 · 3ч 46м

#### PEPE-test-narrow-v1 · 1000PEPE-USDT · spreads 0.001/0.0025 · refresh 20с
Итог:    -$0.49 ❌
Volume:  $1.8K
TP=24 · SL=10 · EARLY_STOP=57
**Вывод:** fills есть, но SL=0.005 слишком близко — 10 SL съедают 24 TP

#### PEPE-test-wide-v8 · 1000PEPE-USDC · spreads 0.002/0.004 · refresh 120с
Итог:    +$0.19 ✅
Volume:  $300
TRAILING_STOP=4 · EARLY_STOP=4
**Вывод:** редкие но качественные fills · trailing_stop фиксирует прибыль

**Паттерн:** не количество fills важно, а соотношение TP/SL.
Narrow: 24 TP но 10 SL их перекрывают → минус.
Wide: 4 trailing → плюс.

**Вывод:** wide-v8 паттерн рабочий. Развивать.
Для narrow: увеличить stop_loss 0.005 → 0.015-0.02
или заменить SL на trailing_stop как в wide-v8.

**Конфиг wide-v8:** spreads 0.002/0.004 · refresh 120с · 
stop_loss 0.02 · take_profit 0.008 · 
trailing_stop activation 0.006 · delta 0.003 · macd_slow 180

---
## 2026-06-16 ночь · Asia сессия
### PEPE-test-wide-v8 · leverage 20 · stop_loss 0.05
Instance: pepe-wide-night-20260616-195815
Старт: ~20:00 UTC (начало Asia)
Конфиг: spreads 0.002/0.004 · refresh 120с · leverage 20 · SL 0.05 · TP 0.008
Изменения vs днём: leverage 5→20, stop_loss 0.02→0.05
Цель: проверить Asia без токсичных SL срабатываний
narrow-v1 остановлен — доказанно убыточен
Результат: TODO утром

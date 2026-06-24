"""
gaussian_mm_imbalance.py — tanh-baseline + imbalance filter.

Фильтр основан на находке из анализа bookDepth (сессия 2026-06-24):
  bid-heavy стакан (imb > 0.55) → цена идёт ВНИЗ (контринтуитивно)
  → блокируем BID (не покупаем в bid wall)
  ask-heavy стакан (imb < 0.45) → цена идёт ВВЕРХ
  → блокируем ASK (не продаём когда спрос давит вверх)

Пороги 0.45/0.55 из анализа: mean=0.522, std=0.056 →
  0.45 ≈ mean - 1.3*std (зона заметного ask-давления)
  0.55 ≈ mean + 0.5*std (зона bid wall)

get_orders возвращает "заблокированный" уровень как цену за пределами
досягаемости рынка (bid=0 / ask=price*10), а не None — это сохраняет
совместимость с engine.py, который проверяет `price <= bid_price`.
"""

import math


def get_orders(price, config, position):
    imbalance = config.get("current_imbalance", 0.5)
    imb_bid_block  = config.get("imb_bid_block",  0.55)  # выше → не покупаем
    imb_ask_block  = config.get("imb_ask_block",  0.45)  # ниже → не продаём

    # --- tanh skew (baseline из сессии 2026-06-21) ---
    lot_size = config.get("lot_size", 0)
    position_in_lots = position / lot_size if lot_size > 0 else 0.0
    max_skew = config.get("max_skew_pct", 0.01)
    sensitivity = config.get("inventory_skew_mult", 0.005)
    skew = max_skew * math.tanh(position_in_lots * sensitivity)
    reference_price = price * (1 - skew)

    buy_spread  = config["buy_spreads"][0]
    sell_spread = config["sell_spreads"][0]

    bid = reference_price * (1 - buy_spread)
    ask = reference_price * (1 + sell_spread)

    # --- imbalance filter ---
    # bid wall → цена пойдёт вниз → блокируем покупку
    if imbalance > imb_bid_block:
        bid = 0.0               # price <= 0 никогда не выполнится

    # ask wall → цена пойдёт вверх → блокируем продажу
    if imbalance < imb_ask_block:
        ask = price * 10.0      # price >= price*10 никогда не выполнится

    bid_spread_pct = buy_spread  * 100
    ask_spread_pct = sell_spread * 100

    return bid, ask, bid_spread_pct, ask_spread_pct

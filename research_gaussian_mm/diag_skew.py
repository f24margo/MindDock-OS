"""
diag_skew.py — временная диагностика для разбора аномального убытка
при spread=0.05%/skew=0.02 (сессия 2026-06-19, после grid search).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import load_agg_trades, load_book_depth, get_available_depth
from strategies import gaussian_mm

DATA_DIR = "data_raw"
SYMBOL = "1000PEPEUSDT"
DATE = "2026-06-18"

trades = load_agg_trades(os.path.join(DATA_DIR, f"{SYMBOL}-aggTrades-{DATE}.csv"))
book = load_book_depth(os.path.join(DATA_DIR, f"{SYMBOL}-bookDepth-{DATE}.csv"))

config = {
    "fee": 0.0004,
    "max_position_limit": 20000000.0,
    "inventory_skew_mult": 0.02,
    "max_order_age": 750,
    "buy_spreads": [0.0005, 0.001],
    "sell_spreads": [0.0005, 0.001],
    "lot_size": 0.01,
}

lot_size = config["lot_size"]
fee = config["fee"]
max_pos = config["max_position_limit"]
max_order_age = config["max_order_age"]

position = 0.0
inv_cost = 0.0
realized_pnl = 0.0
total_fees = 0.0

bid_price = ask_price = None
bid_spread_pct = ask_spread_pct = None
last_order_update_idx = -max_order_age

peak_position = 0.0
trough_position = 0.0
min_bid = float("inf")
max_ask = float("-inf")
negative_bid_count = 0
extreme_skew_events = []

import pandas as pd
import numpy as np

book_reset = book.reset_index().rename(columns={"index": "timestamp"})
merged_book = pd.merge_asof(
    trades[["timestamp"]], book_reset, on="timestamp", direction="backward"
)

for i in range(len(trades)):
    row = trades.iloc[i]
    price = row["price"]
    qty = row["quantity"]
    taker_sold = row["is_buyer_maker"]

    if bid_price is None or (i - last_order_update_idx) >= max_order_age:
        bid_price, ask_price, bid_spread_pct, ask_spread_pct = gaussian_mm.get_orders(
            price, config, position
        )
        last_order_update_idx = i

        skew_now = position * config["inventory_skew_mult"]
        if abs(skew_now) > 0.01:
            extreme_skew_events.append((i, position, skew_now, bid_price, ask_price))

        if bid_price < 0:
            negative_bid_count += 1
        min_bid = min(min_bid, bid_price)
        max_ask = max(max_ask, ask_price)

        continue

    book_row = merged_book.iloc[i]

    if taker_sold and bid_price is not None and price <= bid_price:
        if (position + lot_size) <= max_pos:
            available = get_available_depth(book_row, bid_spread_pct, "bid")
            fill_qty = min(lot_size, qty, available)
            if fill_qty > 0:
                if position >= 0:
                    inv_cost = ((position * inv_cost) + (fill_qty * bid_price)) / (position + fill_qty)
                else:
                    realized_pnl += fill_qty * (inv_cost - bid_price)
                position += fill_qty
                total_fees += bid_price * fill_qty * fee
                last_order_update_idx = i - max_order_age

    if (not taker_sold) and ask_price is not None and price >= ask_price:
        if (position - lot_size) >= -max_pos:
            available = get_available_depth(book_row, ask_spread_pct, "ask")
            fill_qty = min(lot_size, qty, available)
            if fill_qty > 0:
                if position <= 0:
                    inv_cost = ((abs(position) * inv_cost) + (fill_qty * ask_price)) / (abs(position) + fill_qty)
                else:
                    realized_pnl += fill_qty * (ask_price - inv_cost)
                position -= fill_qty
                total_fees += ask_price * fill_qty * fee
                last_order_update_idx = i - max_order_age

    peak_position = max(peak_position, position)
    trough_position = min(trough_position, position)

print(f"Пиковая позиция (max):  {peak_position:.4f}")
print(f"Пиковая позиция (min):  {trough_position:.4f}")
print(f"Min bid когда-либо был: {min_bid}")
print(f"Max ask когда-либо был: {max_ask}")
print(f"Случаев bid < 0:        {negative_bid_count}")
print(f"Realized PnL:           {realized_pnl:.6f}")
print(f"Total fees:             {total_fees:.6f}")
print()
print(f"Экстремальных skew-событий (|skew|>1%): {len(extreme_skew_events)}")
if extreme_skew_events:
    print("Первые 10:")
    for idx, pos, skew, bid, ask in extreme_skew_events[:10]:
        print(f"  i={idx}: position={pos:.4f}, skew={skew:.6f}, bid={bid:.8f}, ask={ask:.8f}")

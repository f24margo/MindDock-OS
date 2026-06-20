"""
engine.py — bookDepth-aware matching engine для gaussian_mm бэктеста.
ЗАФИКСИРОВАННЫЕ ДОПУЩЕНИЯ (сессия 2026-06-19):
1. Ступенчатая интерполяция bucket'ов (ближайший больший по модулю).
2. Fill капается доступным объёмом bookDepth, остаток тика игнорируется.
3. Твой ордер не влияет на bookDepth (price-taker assumption).
4. Объём на уровне восстанавливается каждый тик (upper-bound на fill rate).

PnL считается способом A: realized_pnl только от закрытия позиции
(против inv_cost — средневзвешенной цены входа), комиссии отдельно
в total_fees, unrealized_pnl — оценка незакрытой позиции по последней
цене дня. total_pnl = realized_pnl - total_fees + unrealized_pnl.
"""

import numpy as np
import pandas as pd
from bisect import bisect_left

BID_BUCKETS = sorted([-5.00, -4.00, -3.00, -2.00, -1.00, -0.20])
ASK_BUCKETS = sorted([0.20, 1.00, 2.00, 3.00, 4.00, 5.00])


def load_book_depth(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["timestamp"] = df["timestamp"].astype("datetime64[ms]")
    df["side"] = np.where(df["percentage"] < 0, "bid", "ask")
    pivot = df.pivot_table(
        index="timestamp", columns=["side", "percentage"], values="depth"
    )
    pivot.columns = [f"{side}_{pct:.2f}" for side, pct in pivot.columns]
    return pivot.sort_index()


def load_agg_trades(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["transact_time"], unit="ms").astype("datetime64[ms]")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df[["timestamp", "price", "quantity", "is_buyer_maker"]]


def nearest_bucket_ceiling(spread_pct: float, side: str) -> float:
    buckets = BID_BUCKETS if side == "bid" else ASK_BUCKETS
    abs_buckets = sorted(abs(b) for b in buckets)
    idx = bisect_left(abs_buckets, spread_pct)
    if idx >= len(abs_buckets):
        idx = len(abs_buckets) - 1
    return abs_buckets[idx]


def get_available_depth(book_row: pd.Series, spread_pct: float, side: str) -> float:
    bucket = nearest_bucket_ceiling(spread_pct, side)
    sign = -1 if side == "bid" else 1
    col = f"{side}_{sign * bucket:.2f}"
    if col not in book_row.index or pd.isna(book_row[col]):
        return 0.0
    return float(book_row[col])


def run_simulation(trades: pd.DataFrame, book: pd.DataFrame, get_signals_func, config: dict) -> dict:
    lot_size = config.get("lot_size", 0.01)
    fee = config["fee"]
    max_pos = config["max_position_limit"]
    max_order_age = config["max_order_age"]

    position = 0.0
    inv_cost = 0.0
    realized_pnl = 0.0
    total_fees = 0.0
    total_trades = 0
    fills_capped_by_depth = 0
    positions = []

    bid_price = ask_price = None
    bid_spread_pct = ask_spread_pct = None
    last_order_update_idx = -max_order_age

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
            bid_price, ask_price, bid_spread_pct, ask_spread_pct = get_signals_func(
                price, config, position
            )
            last_order_update_idx = i
            positions.append(position)
            continue

        book_row = merged_book.iloc[i]

        if taker_sold and bid_price is not None and price <= bid_price:
            if (position + lot_size) <= max_pos:
                available = get_available_depth(book_row, bid_spread_pct, "bid")
                fill_qty = min(lot_size, qty, available)
                if available < min(lot_size, qty):
                    fills_capped_by_depth += 1
                if fill_qty > 0:
                    if position >= 0:
                        inv_cost = ((position * inv_cost) + (fill_qty * bid_price)) / (position + fill_qty)
                    else:
                        realized_pnl += fill_qty * (inv_cost - bid_price)
                    position += fill_qty
                    total_fees += bid_price * fill_qty * fee
                    total_trades += 1
                    last_order_update_idx = i - max_order_age

        if (not taker_sold) and ask_price is not None and price >= ask_price:
            if (position - lot_size) >= -max_pos:
                available = get_available_depth(book_row, ask_spread_pct, "ask")
                fill_qty = min(lot_size, qty, available)
                if available < min(lot_size, qty):
                    fills_capped_by_depth += 1
                if fill_qty > 0:
                    if position <= 0:
                        inv_cost = ((abs(position) * inv_cost) + (fill_qty * ask_price)) / (abs(position) + fill_qty)
                    else:
                        realized_pnl += fill_qty * (ask_price - inv_cost)
                    position -= fill_qty
                    total_fees += ask_price * fill_qty * fee
                    total_trades += 1
                    last_order_update_idx = i - max_order_age

        positions.append(position)

    avg_inventory = float(np.mean(np.abs(positions))) if positions else 0.0

    last_price = float(trades["price"].iloc[-1]) if len(trades) > 0 else 0.0
    if position > 0:
        unrealized_pnl = position * (last_price - inv_cost)
    elif position < 0:
        unrealized_pnl = abs(position) * (inv_cost - last_price)
    else:
        unrealized_pnl = 0.0

    total_pnl = realized_pnl - total_fees + unrealized_pnl

    return {
        "total_trades": total_trades,
        "realized_pnl": realized_pnl,
        "total_fees": total_fees,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": total_pnl,
        "avg_inventory": avg_inventory,
        "final_position": position,
        "inv_cost": inv_cost,
        "fills_capped_by_depth": fills_capped_by_depth,
    }

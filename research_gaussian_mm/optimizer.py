"""
optimizer.py — тонкая настройка grid search вокруг spread=0.3%/skew=0
(лучшая зона из предыдущего широкого прогона после фикса skew-бага).
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import run_simulation, load_book_depth, load_agg_trades
from strategies import gaussian_mm


DATA_DIR = "data_raw"
SYMBOL = "1000PEPEUSDT"
DATE = "2026-06-18"


def load_data():
    agg_path = os.path.join(DATA_DIR, f"{SYMBOL}-aggTrades-{DATE}.csv")
    book_path = os.path.join(DATA_DIR, f"{SYMBOL}-bookDepth-{DATE}.csv")

    if not os.path.exists(agg_path) or not os.path.exists(book_path):
        raise FileNotFoundError(
            f"Не найдены файлы в {DATA_DIR}/. Ожидались:\n  {agg_path}\n  {book_path}"
        )

    print(f"Загружаю aggTrades из {agg_path} ...")
    trades = load_agg_trades(agg_path)
    print(f"  -> {len(trades):,} тиков, диапазон {trades['timestamp'].iloc[0]} — {trades['timestamp'].iloc[-1]}")

    print(f"Загружаю bookDepth из {book_path} ...")
    book = load_book_depth(book_path)
    print(f"  -> {len(book):,} снэпшотов, колонки: {list(book.columns)}")

    return trades, book


config = {
    "leverage": 20,
    "fee": 0.0004,
    "max_position_limit": 20000000.0,
    "total_amount_quote": 100.0,
    "inventory_skew_mult": 0.05,
    "max_order_age": 50,
    "buy_spreads": [0.003, 0.006],
    "sell_spreads": [0.003, 0.006],
    "cooldown_time": 15,
    "lot_size": 0.01,
}


if __name__ == "__main__":
    trades, book = load_data()

    print()
    print("Grid search (тонкая настройка вокруг spread=0.3%/skew=0), age=750")
    print(f"{'Spread':<8} | {'Skew':<7} | {'Trades':<7} | {'Realized':<11} | {'Fees':<10} | {'Unreal':<11} | {'Total PnL':<12} | {'AvgInv':<8}")
    print("-" * 100)

    config["max_order_age"] = 750

    spread_grid = [0.0025, 0.0028, 0.003, 0.0032, 0.0035, 0.004, 0.0045, 0.005]
    skew_grid = [0.0, 0.005, 0.01, 0.02]

    results = []
    for spread in spread_grid:
        for skew in skew_grid:
            config["buy_spreads"] = [spread, spread * 2]
            config["sell_spreads"] = [spread, spread * 2]
            config["inventory_skew_mult"] = skew
            result = run_simulation(trades, book, gaussian_mm.get_orders, config)
            results.append((spread, skew, result))
            print(
                f"{spread*100:<8.3f} | {skew:<7.3f} | {result['total_trades']:<7} | "
                f"{result['realized_pnl']:<11.6f} | {result['total_fees']:<10.6f} | "
                f"{result['unrealized_pnl']:<11.6f} | {result['total_pnl']:<12.6f} | "
                f"{result['avg_inventory']:<8.4f}"
            )

    print()
    best = max(results, key=lambda r: r[2]["total_pnl"])
    print(f"Лучшая комбинация: spread={best[0]*100:.3f}%, skew={best[1]:.3f}, "
          f"Total PnL={best[2]['total_pnl']:.6f}, trades={best[2]['total_trades']}")

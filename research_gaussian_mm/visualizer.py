"""
visualizer.py — диагностика bookDepth-aware движка на реальных aggTrades.

Показывает:
  1) Цену тика + ДВИЖУЩИЙСЯ коридор bid/ask (пересчитывается каждые
     max_order_age тиков от текущей цены — не зафиксирован от старта)
  2) Точки фактических филлов (если есть)
  3) Второй сабплот: % расстояние цены до bid (пилообразный паттерн
     показывает, убегает ли коридор от цены)

Использование:
  python3 visualizer.py --age 300 --spread 0.003 --start 0 --end 10000
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

from engine import load_agg_trades


def simulate_for_plot(prices, taker_sold_flags, max_order_age, spread, skew_mult, lot_size):
    position = 0.0
    bid_price = ask_price = None
    last_update = -max_order_age

    bid_series = np.full(len(prices), np.nan)
    ask_series = np.full(len(prices), np.nan)
    fill_idx = []
    fill_side = []

    for i in range(len(prices)):
        price = prices[i]
        taker_sold = taker_sold_flags[i]

        if bid_price is None or (i - last_update) >= max_order_age:
            skew = position * skew_mult
            bid_price = price * (1 - spread - skew)
            ask_price = price * (1 + spread + skew)
            last_update = i
            bid_series[i] = bid_price
            ask_series[i] = ask_price
            continue

        bid_series[i] = bid_price
        ask_series[i] = ask_price

        if taker_sold and price <= bid_price:
            fill_idx.append(i)
            fill_side.append("bid")
            position += lot_size
            last_update = i - max_order_age
        elif (not taker_sold) and price >= ask_price:
            fill_idx.append(i)
            fill_side.append("ask")
            position -= lot_size
            last_update = i - max_order_age

    return bid_series, ask_series, fill_idx, fill_side


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data_raw")
    parser.add_argument("--symbol", default="1000PEPEUSDT")
    parser.add_argument("--date", default="2026-06-18")
    parser.add_argument("--age", type=int, default=300)
    parser.add_argument("--spread", type=float, default=0.003)
    parser.add_argument("--skew-mult", type=float, default=0.05)
    parser.add_argument("--lot-size", type=float, default=0.01)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=10000)
    args = parser.parse_args()

    agg_path = f"{args.data_dir}/{args.symbol}-aggTrades-{args.date}.csv"
    trades = load_agg_trades(agg_path)

    print(f"Загружено {len(trades):,} тиков из {agg_path}")
    print(f"Симулирую коридор bid/ask: age={args.age}, spread={args.spread*100:.3f}%")

    prices = trades["price"].values
    taker_sold = trades["is_buyer_maker"].values

    bid_series, ask_series, fill_idx, fill_side = simulate_for_plot(
        prices, taker_sold, args.age, args.spread, args.skew_mult, args.lot_size
    )

    print(f"Всего филлов на полном дне (упрощённая геометрия, без bookDepth-капа): {len(fill_idx)}")

    start_idx = max(0, args.start)
    end_idx = min(len(prices), args.end)

    t = np.arange(start_idx, end_idx)
    price_slice = prices[start_idx:end_idx]
    bid_slice = bid_series[start_idx:end_idx]
    ask_slice = ask_series[start_idx:end_idx]

    fills_in_range = [(i, s) for i, s in zip(fill_idx, fill_side) if start_idx <= i < end_idx]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1]})

    ax1.plot(t, price_slice, label="Цена (тик)", color="blue", linewidth=0.8, alpha=0.7)
    ax1.plot(t, bid_slice, label="Bid (движущийся)", color="green", linewidth=0.8, linestyle="--")
    ax1.plot(t, ask_slice, label="Ask (движущийся)", color="red", linewidth=0.8, linestyle="--")

    if fills_in_range:
        bid_fills = [i for i, s in fills_in_range if s == "bid"]
        ask_fills = [i for i, s in fills_in_range if s == "ask"]
        if bid_fills:
            ax1.scatter(bid_fills, prices[bid_fills], color="green", marker="^", s=60,
                        zorder=5, label=f"Bid fills ({len(bid_fills)})")
        if ask_fills:
            ax1.scatter(ask_fills, prices[ask_fills], color="red", marker="v", s=60,
                        zorder=5, label=f"Ask fills ({len(ask_fills)})")

    ax1.set_title(
        f"Движущийся коридор bid/ask — age={args.age} тиков, "
        f"spread={args.spread*100:.2f}%, окно тиков [{start_idx}:{end_idx}]"
    )
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel("Цена")

    bid_dist_pct = (price_slice - bid_slice) / price_slice * 100
    ax2.plot(t, bid_dist_pct, color="green", linewidth=0.7, label="Цена выше bid на, %")
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_xlabel("Индекс тика")
    ax2.set_ylabel("% до bid")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("visualizer_output.png", dpi=120)
    print("Сохранено в visualizer_output.png")
    plt.show()


if __name__ == "__main__":
    main()

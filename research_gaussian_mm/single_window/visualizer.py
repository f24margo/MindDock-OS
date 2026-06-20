import matplotlib.pyplot as plt
import pandas as pd

def plot_window_diagnostics(df_trades_slice: pd.DataFrame,
                            get_signals_func,
                            config: dict,
                            start_ts: int,
                            end_ts: int,
                            save_path: str = None):
    """
    Генерирует диагностические графики.
    По контракту run_simulation не возвращает тиковые ряды. Поэтому модуль визуализации
    выполняет изолированный легковесный проход для расчета геометрии коридоров,
    не затрагивая ядро матчинга.

    ИСПРАВЛЕНО: get_orders() в strategies/gaussian_mm.py уже возвращает
    bid_spread_pct = buy_spread * 100, то есть значение УЖЕ в процентах
    (например 0.3 для spread=0.003). Предыдущая версия домножала на 100
    повторно, получая 30.0 вместо 0.3 — график не падал, но ось Y была
    в 100 раз больше реальной. Здесь убрано.
    """
    if df_trades_slice.empty:
        raise ValueError("Пустой датафрейм сделок для визуализации.")

    bid_corridor = []
    ask_corridor = []
    price_to_bid_dist = []  # номинальный bid_spread_pct из стратегии, УЖЕ в процентах
    timestamps = []

    current_position = 0.0  # Изолированный трекинг геометрии без учета исполнения стакана

    for _, row in df_trades_slice.iterrows():
        price = row['price']
        ts = row['timestamp']

        bid_p, ask_p, bid_spd, _ = get_signals_func(price, config, current_position)

        bid_corridor.append(bid_p)
        ask_corridor.append(ask_p)
        price_to_bid_dist.append(float(bid_spd))
        timestamps.append(pd.to_datetime(ts, unit='ms'))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    ax1.plot(timestamps, df_trades_slice['price'], label='Mid Price', color='black', alpha=0.4)
    ax1.plot(timestamps, bid_corridor, label='MM Bid Line', color='green', linestyle='--')
    ax1.plot(timestamps, ask_corridor, label='MM Ask Line', color='red', linestyle='--')
    ax1.set_title(f"MM Corridor Geometric Tracking ({pd.to_datetime(start_ts, unit='ms')} UTC)")
    ax1.set_ylabel("Price")
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.2)

    # Это НОМИНАЛЬНЫЙ spread из конфига стратегии (buy_spreads[0]*100),
    # НЕ фактическое расстояние цены до выставленного bid (отличается
    # из-за inventory skew). Для фактического расстояния:
    # (price - bid_corridor) / price * 100
    ax2.plot(timestamps, price_to_bid_dist, color='blue', label='Nominal bid spread, % (from config)')
    ax2.set_ylabel("Spread (%)")
    ax2.set_xlabel("Time (UTC)")
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.2)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

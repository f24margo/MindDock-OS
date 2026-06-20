import pandas as pd

def slice_window(df_trades: pd.DataFrame, df_depth: pd.DataFrame,
                 start_ts: int, end_ts: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Выделяет временное окно из данных aggTrades и bookDepth.

    Проверено: колонка timestamp в df_trades и индекс timestamp в df_depth
    соответствуют реальным load_agg_trades()/load_book_depth() из engine.py.
    """
    trades_mask = (df_trades['timestamp'] >= start_ts) & (df_trades['timestamp'] <= end_ts)
    depth_mask = (df_depth.index >= start_ts) & (df_depth.index <= end_ts)

    df_trades_slice = df_trades.loc[trades_mask].copy()
    df_depth_slice = df_depth.loc[depth_mask].copy()

    print("=" * 50)
    print(f"--- DIAGNOSTIC WINDOW INFO [{start_ts} -> {end_ts}] ---")
    print(f"Total aggTrades ticks in window: {len(df_trades_slice)}")
    print(f"Total bookDepth snapshots in window: {len(df_depth_slice)}")

    if not df_trades_slice.empty:
        print(f"First tick time (UTC): {pd.to_datetime(df_trades_slice['timestamp'].iloc[0], unit='ms')}")
        print(f"Last tick time (UTC):  {pd.to_datetime(df_trades_slice['timestamp'].iloc[-1], unit='ms')}")
    else:
        print("WARNING: окно не содержит ни одного тика — проверь start_ts/end_ts.")

    if df_depth_slice.empty:
        print("WARNING: окно не содержит ни одного bookDepth снэпшота.")
    print("=" * 50)

    return df_trades_slice, df_depth_slice


def calculate_max_order_age(day_ticks: int, window_trades_len: int, base_age_day: int = 750) -> int:
    """
    Пересчитывает max_order_age пропорционально размеру окна.
    Нижний защитный порог = 300 тиков (на полнодневных данных 1000PEPEUSDT
    age < 300 систематически давал 0 сделок — котировка переустанавливается
    быстрее, чем цена успевает её догнать при spread~0.3%).

    ВАЖНО: этот порог откалиброван на ОДНОЙ паре (1000PEPEUSDT) и ОДНОМ
    дне. При переносе на другую пару/период — проверить заново через
    visualizer.py, не считать 300 универсальной константой.
    """
    if day_ticks == 0:
        return base_age_day

    proportional_age = int((window_trades_len / day_ticks) * base_age_day)
    return max(proportional_age, 300)

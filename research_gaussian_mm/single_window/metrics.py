import sys
def run_window_backtest_and_metrics(df_trades_slice, df_depth_slice, get_signals_func, config: dict) -> dict:
    # Динамически берем уже загруженный движок из sys.modules
    target_engine = sys.modules.get("target_engine")
    if not target_engine:
        raise ImportError("Модуль target_engine должен быть загружен в Ячейке 1")

    sim_result = target_engine.run_simulation(df_trades_slice, df_depth_slice, get_signals_func, config)
    return {
        "total_trades": sim_result.get("total_trades", 0),
        "realized_pnl": sim_result.get("realized_pnl", 0.0),
        "total_fees": sim_result.get("total_fees", 0.0),
        "unrealized_pnl": sim_result.get("unrealized_pnl", 0.0),
        "total_pnl": sim_result.get("total_pnl", 0.0), 
        "avg_inventory": sim_result.get("avg_inventory", 0.0),
        "final_position": sim_result.get("final_position", 0.0),
        "fills_capped_by_depth": sim_result.get("fills_capped_by_depth", 0)
    }

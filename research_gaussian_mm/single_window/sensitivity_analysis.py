import sys
def analyze_parameter_sensitivity(df_trades_slice, df_depth_slice, get_signals_func, base_config: dict, param_name: str, scan_range: list):
    sw_metrics = sys.modules.get("sw_metrics")
    import pandas as pd
    results = []
    working_config = base_config.copy()
    for value in scan_range:
        working_config[param_name] = value
        metrics = sw_metrics.run_window_backtest_and_metrics(df_trades_slice, df_depth_slice, get_signals_func, working_config)
        results.append({param_name: value, "total_trades": metrics["total_trades"], "total_pnl": metrics["total_pnl"], "avg_inventory": metrics["avg_inventory"]})
    return pd.DataFrame(results)

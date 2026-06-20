def calculate_lot_size(total_amount_quote: float, current_price: float, leverage: float) -> float:
    """
    Размер лота В ЕДИНИЦАХ БАЗОВОГО АКТИВА (PEPE), напрямую — без деления
    на 1000. run_simulation в engine.py трактует config["lot_size"] как
    количество единиц актива в одной сделке (position += fill_qty), без
    какого-либо понятия о "контрактах" — поэтому здесь оставлены простые
    единицы, не приведение к фьючерсному контракту 1000PEPEUSDT.

    Допущение: один лот = 1% от полного номинала (total_amount_quote *
    leverage / price). Произвольное допущение — проверь под свою модель
    риска перед использованием для реальных решений о размере позиции.
    """
    if current_price <= 0:
        return 0.0
    total_nominal_crypto = (total_amount_quote * leverage) / current_price
    return total_nominal_crypto * 0.01


MM_ENGINE_CONFIG = {
    "symbol": "1000PEPEUSDT",
    "total_amount_quote": 100.0,
    "leverage": 20.0,

    "fee": 0.0002,

    "max_position_limit": 5000000.0,
    "inventory_skew_mult": 0.005,
    "cooldown_time": 15,
    "buy_spreads": [0.0025, 0.005],
    "sell_spreads": [0.0025, 0.005],
}

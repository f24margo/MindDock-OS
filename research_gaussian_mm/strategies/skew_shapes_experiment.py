"""
skew_shapes_experiment.py — сравнение РАЗНЫХ ФОРМ функции skew (не просто
разных значений одного параметра), чтобы понять архитектурный вопрос:
есть ли форма зависимости от инвентаря, которая не требует "искать
маленькое окно настроек" (как линейная формула вынуждает делать —
см. найденный сегодня bell-shaped optimum при skew_mult~0.0005, что по
сути означает "почти выключенный skew", а не разумную защиту).

Все 4 варианта используют ту же базовую геометрию (reference_price сдвиг,
симметричный спред вокруг него), отличается только функция skew(position).
"""

import math


def get_orders_linear(price, config, current_position):
    """БАЗОВЫЙ ВАРИАНТ (текущий в strategies/gaussian_mm.py).
    skew растёт ЛИНЕЙНО и НЕОГРАНИЧЕННО с position_in_lots."""
    lot_size = config.get("lot_size", 0)
    position_in_lots = current_position / lot_size if lot_size > 0 else 0.0

    skew = position_in_lots * config["inventory_skew_mult"]
    return _build_orders(price, config, skew)


def get_orders_hardcap(price, config, current_position):
    """Линейная формула, но сдвиг ОБРЕЗАН сверху по модулю — не позволяет
    коридору улетать сколь угодно далеко при больших позициях."""
    lot_size = config.get("lot_size", 0)
    position_in_lots = current_position / lot_size if lot_size > 0 else 0.0

    raw_skew = position_in_lots * config["inventory_skew_mult"]
    max_skew = config.get("max_skew_pct", 0.01)
    skew = max(-max_skew, min(max_skew, raw_skew))
    return _build_orders(price, config, skew)


def get_orders_tanh(price, config, current_position):
    """Плавно выходит на плато через tanh — быстрый рост на малых
    позициях (реальная защита), насыщение на больших (не улетает)."""
    lot_size = config.get("lot_size", 0)
    position_in_lots = current_position / lot_size if lot_size > 0 else 0.0

    max_skew = config.get("max_skew_pct", 0.01)
    sensitivity = config["inventory_skew_mult"]
    skew = max_skew * math.tanh(position_in_lots * sensitivity)
    return _build_orders(price, config, skew)


def get_orders_log(price, config, current_position):
    """Логарифмический рост — медленнее линейного, но без жёсткого
    потолка (продолжает расти, просто всё медленнее)."""
    lot_size = config.get("lot_size", 0)
    position_in_lots = current_position / lot_size if lot_size > 0 else 0.0

    sign = 1.0 if position_in_lots >= 0 else -1.0
    skew = sign * config["inventory_skew_mult"] * math.log1p(abs(position_in_lots))
    return _build_orders(price, config, skew)


def _build_orders(price, config, skew):
    """Общая геометрия для всех вариантов — отличается только сам skew."""
    reference_price = price * (1 - skew)

    buy_spread = config["buy_spreads"][0]
    sell_spread = config["sell_spreads"][0]

    bid = reference_price * (1 - buy_spread)
    ask = reference_price * (1 + sell_spread)

    bid_spread_pct = buy_spread * 100
    ask_spread_pct = sell_spread * 100

    return bid, ask, bid_spread_pct, ask_spread_pct

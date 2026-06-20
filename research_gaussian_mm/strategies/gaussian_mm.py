def get_orders(price, config, current_position):
    """
    ИСПРАВЛЕНО (2026-06-19, после анализа grid search): старая формула
    сдвигала bid и ask в ПРОТИВОПОЛОЖНЫХ направлениях относительно skew
    (bid = price*(1-spread-skew), ask = price*(1+spread+skew)). При
    position < 0 (шорт) это давало skew < 0, из-за чего ask приближался
    к цене (наращивание шорта становилось привлекательнее) вместо того
    чтобы отдаляться от неё (что снизило бы риск). При достаточно
    большом |skew| канал мог даже инвертироваться (ask < bid).

    Новая формула сдвигает ОБЩИЙ reference price (центр канала), сохраняя
    симметричный спред вокруг него — стандартный подход (в духе
    Avellaneda-Stoikov reservation price). При шорте reference растёт,
    то есть ОБА — и bid, и ask — сдвигаются вверх: охотнее закрываем
    шорт (bid ближе к рынку относительно ask) И неохотнее наращиваем
    его дальше (ask дальше от рынка относительно bid).
    """
    skew = current_position * config["inventory_skew_mult"]
    reference_price = price * (1 - skew)

    buy_spread = config["buy_spreads"][0]
    sell_spread = config["sell_spreads"][0]

    bid = reference_price * (1 - buy_spread)
    ask = reference_price * (1 + sell_spread)

    bid_spread_pct = buy_spread * 100
    ask_spread_pct = sell_spread * 100

    return bid, ask, bid_spread_pct, ask_spread_pct

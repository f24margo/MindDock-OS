def get_orders(price, config, current_position):
    """
    ИСПРАВЛЕНО (2026-06-19): sign error в skew — старая формула сдвигала
    bid и ask в противоположных направлениях, что при шорте делало
    наращивание позиции привлекательнее вместо защиты от риска. Заменено
    на сдвиг общего reference_price (Avellaneda-Stoikov style).

    ИСПРАВЛЕНО (2026-06-20): переполнение skew при большом lot_size.
    Формула skew = current_position * inventory_skew_mult была откалибро-
    вана на малых position (единицы PEPE). При lot_size=6898 одна сделка
    сразу даёт position=6898, и skew = 6898 * 0.005 = 34.49 (3449%
    сдвига) — reference_price уходил в отрицательные числа, bid/ask
    становились отрицательными, движок честно матчил ордера по этим
    ценам, что дало realized_pnl на уровне -469093 за 1877 сделок при
    notional одного лота ~$20.

    Теперь skew нормализован через current_position / lot_size — то
    есть выражен в ДОЛЯХ ОТ ОДНОГО ЛОТА. При position = 1 лот, skew =
    inventory_skew_mult ровно. При 10 лотах — в 10 раз больше, линейно
    и предсказуемо вне зависимости от абсолютного масштаба lot_size.
    """
    lot_size = config.get("lot_size", 0)
    if lot_size > 0:
        position_in_lots = current_position / lot_size
    else:
        position_in_lots = 0.0

    skew = position_in_lots * config["inventory_skew_mult"]
    reference_price = price * (1 - skew)

    buy_spread = config["buy_spreads"][0]
    sell_spread = config["sell_spreads"][0]

    bid = reference_price * (1 - buy_spread)
    ask = reference_price * (1 + sell_spread)

    bid_spread_pct = buy_spread * 100
    ask_spread_pct = sell_spread * 100

    return bid, ask, bid_spread_pct, ask_spread_pct

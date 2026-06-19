import numpy as np

def load_market_cache(path: str = "cache/market_cache.npz") -> dict:
    data = np.load(path, allow_pickle=True)
    return {key: data[key] for key in data.files}

if __name__ == "__main__":
    print("Шаг 10.1: Инициализация симулятора ордеров (Elastic Spread)...")
    
    try:
        cache = load_market_cache()
        close_prices = cache['close']
        high_prices = cache['high']
        low_prices = cache['low']
        gauss_center = cache['gauss_center']
        natr = cache['natr']
        
        GAUSS_DISTANCE_BASE = 1.678  
        MIN_NATR = 0.0005            
        MAX_NATR = 0.02              
        WARMUP_PERIOD = 7044         
        SPREAD_ELASTICITY = 0.0005  

        el_position = 0.0
        el_realized_pnl = 0.0
        el_total_trades = 0
        el_inv_cost = 0.0

        print("Шаг 10.2: Запуск матчинга по секундным барам...")
        for i in range(len(close_prices)):
            if i < WARMUP_PERIOD:
                continue
                
            current_center = gauss_center[i]
            current_high = high_prices[i]
            current_low = low_prices[i]
            current_natr = natr[i]
            
            if current_natr > MAX_NATR or current_natr < MIN_NATR:
                continue
                
            base_spread = (current_natr / 100.0) * GAUSS_DISTANCE_BASE
            
            ask_modifier = 1.0 + max(0.0, -el_position * SPREAD_ELASTICITY)
            bid_modifier = 1.0 - min(0.5, -el_position * SPREAD_ELASTICITY)
            
            if el_position > 0:
                bid_modifier = 1.0 + (el_position * SPREAD_ELASTICITY)
                ask_modifier = max(0.5, 1.0 - (el_position * SPREAD_ELASTICITY))
                
            my_el_bid = current_center * (1.0 - base_spread * bid_modifier)
            my_el_ask = current_center * (1.0 + base_spread * ask_modifier)
            
            if current_low <= my_el_bid:
                lot_size = 1.0
                if el_position >= 0:
                    el_inv_cost = ((el_position * el_inv_cost) + (lot_size * my_el_bid)) / (el_position + lot_size)
                else:
                    el_realized_pnl += lot_size * (el_inv_cost - my_el_bid)
                el_position += lot_size
                el_total_trades += 1

            if current_high >= my_el_ask:
                lot_size = 1.0
                if el_position <= 0:
                    el_inv_cost = ((abs(el_position) * el_inv_cost) + (lot_size * my_el_ask)) / (abs(el_position) + lot_size)
                else:
                    el_realized_pnl += lot_size * (my_el_ask - el_inv_cost)
                el_position -= lot_size
                el_total_trades += 1

        # Финальный финансовый аудит
        final_market_price = close_prices[-1]
        if el_position < 0:
            unrealized_pnl = abs(el_position) * (el_inv_cost - final_market_price)
        elif el_position > 0:
            unrealized_pnl = el_position * (final_market_price - el_inv_cost)
        else:
            unrealized_pnl = 0.0

        total_net_pnl = el_realized_pnl + unrealized_pnl

        print(f"\n[РЕЗУЛЬТАТЫ ФИНАНСОВОГО АУДИТА СИМУЛЯТОРА]:")
        print(f"        -> Проторговано HFT-сделок:          {el_total_trades:,}")
        print(f"        -> Реализованный чистый PnL:         {el_realized_pnl:.6f}")
        print(f"        -> Оставшийся инвентарь (Position):  {el_position:.2f}")
        print(f"        -> Плавающий PnL (Unrealized PnL):   {unrealized_pnl:.6f}")
        print(f"        ----------------------------------------------------")
        print(f"        -> ИТОГОВЫЙ МАРЖИНАЛЬНЫЙ TOTAL PNL:   {total_net_pnl:.6f} -> [УСПЕХ]")

    except Exception as e:
        print(f"Ошибка выполнения симулятора: {str(e)}")
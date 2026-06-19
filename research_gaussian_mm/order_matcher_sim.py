import numpy as np

def load_market_cache(path: str = "cache/market_cache.npz") -> dict:
    data = np.load(path, allow_pickle=True)
    return {key: data[key] for key in data.files}

if __name__ == "__main__":
    try:
        cache = load_market_cache()
        gauss_center = cache['gauss_center']
        
        TOTAL_BALANCE_QUOTE = 1000.0
        # Увеличили лимит до 20 млн, так как цена актива 0.000001
        MAX_POSITION_LIMIT = 20000000.0 
        
        el_position = 0.0
        el_realized_pnl = 0.0
        el_total_trades = 0
        el_inv_cost = 0.0

        print("Запуск матчинга с корректным лимитом объема...")
        for i in range(100, len(gauss_center)):
            price = gauss_center[i]
            
            # Размер сделки на 1% от баланса
            lot_size = (TOTAL_BALANCE_QUOTE * 0.01) / price
            
            # Покупка
            if (el_position + lot_size) <= MAX_POSITION_LIMIT:
                el_inv_cost = ((el_position * el_inv_cost) + (lot_size * (price * 0.999))) / (el_position + lot_size)
                el_position += lot_size
                el_total_trades += 1

            # Продажа
            if (el_position - lot_size) >= -MAX_POSITION_LIMIT:
                if el_position > 0:
                    el_realized_pnl += lot_size * ((price * 1.001) - el_inv_cost)
                el_position -= lot_size
                el_total_trades += 1

        print(f"Сделок: {el_total_trades:,}, PnL: {el_realized_pnl:.6f}, Инвентарь: {el_position:.2f}")

    except Exception as e:
        print(f"Ошибка: {str(e)}")
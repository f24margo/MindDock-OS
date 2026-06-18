import numpy as np
import matplotlib.pyplot as plt

def load_market_cache(path: str = "cache/market_cache.npz") -> dict:
    data = np.load(path, allow_pickle=True)
    return {key: data[key] for key in data.files}

if __name__ == "__main__":
    print("Шаг 1: Загрузка данных для визуализации (относительный режим)...")
    try:
        cache = load_market_cache()
        close_prices = cache['close']
        gauss_center = cache['gauss_center']
        natr = cache['natr']
        
        start_idx = 4000
        end_idx = 9000
        
        t = np.arange(start_idx, end_idx)
        price_slice = close_prices[start_idx:end_idx]
        gauss_slice = gauss_center[start_idx:end_idx]
        natr_slice = natr[start_idx:end_idx]
        
        # Расчет в процентах
        price_diff_pct = ((price_slice - gauss_slice) / gauss_slice) * 100
        
        # Динамические каналы
        GAUSS_DISTANCE_BASE = 1.678
        dynamic_spread = (natr_slice / 100.0) * GAUSS_DISTANCE_BASE
        upper_channel_diff = dynamic_spread * 100
        lower_channel_diff = -dynamic_spread * 100
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # --- ВЕРХНИЙ ГРАФИК: Отклонения в % ---
        ax1.plot(t, price_diff_pct, label='Цена (откл. от центра, %)', color='blue', alpha=0.3, lw=1)
        ax1.axhline(0, color='orange', lw=2, label='Математический центр (Гаусс)')
        
        ax1.plot(t, upper_channel_diff, '--', color='red', alpha=0.6, label='Ask (откл. %)')
        ax1.plot(t, lower_channel_diff, '--', color='green', alpha=0.6, label='Bid (откл. %)')
        
        ax1.set_title("HFT-визуализация: Относительная волатильность и спреды", fontsize=14, fontweight='bold')
        ax1.set_ylabel("Отклонение от Gauss (%)", fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.5)
        ax1.legend(loc='upper right')
        
        # --- НИЖНИЙ ГРАФИК: Фильтр волатильности NATR ---
        ax2.plot(t, natr_slice, color='purple', label='Текущий NATR (%)', lw=1.5)
        ax2.axhline(y=0.02, color='red', linestyle=':', label='MAX_NATR (Защита)')
        ax2.set_xlabel("Минутные бары", fontsize=12)
        ax2.set_ylabel("NATR (%)", fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.5)
        ax2.legend(loc='upper left')
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Ошибка визуализации: {str(e)}")
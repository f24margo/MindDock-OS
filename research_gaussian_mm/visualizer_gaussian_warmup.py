import numpy as np
import matplotlib.pyplot as plt

def load_market_cache(path: str = "cache/market_cache.npz") -> dict:
    data = np.load(path, allow_pickle=True)
    return {key: data[key] for key in data.files}

def find_warmup_point(price_diff_pct, window=500, threshold=0.3):
    # Скользящее среднее абсолютного отклонения для поиска стабилизации
    rolling_abs = np.convolve(np.abs(price_diff_pct), np.ones(window)/window, mode='valid')
    stable_indices = np.where(rolling_abs < threshold)[0]
    return stable_indices[0] + window if len(stable_indices) > 0 else 0

if __name__ == "__main__":
    cache = load_market_cache()
    close_prices = cache['close']
    gauss_center = cache['gauss_center']
    natr = cache['natr']
    
    # Берем весь массив для поиска точки прогрева
    full_price_diff = ((close_prices - gauss_center) / gauss_center) * 100
    warmup_idx = find_warmup_point(full_price_diff)
    print(f"!!! ОПРЕДЕЛЕНА ТОЧКА ПРОГРЕВА: {warmup_idx} !!!")
    
    # Визуализируем с запасом от точки прогрева
    start_idx = max(0, warmup_idx - 500)
    end_idx = min(len(close_prices), warmup_idx + 5000)
    
    t = np.arange(start_idx, end_idx)
    price_diff_pct = full_price_diff[start_idx:end_idx]
    natr_slice = natr[start_idx:end_idx]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # График с вертикальной линией прогрева
    ax1.plot(t, price_diff_pct, label='Цена (откл. %)', color='blue', alpha=0.3)
    ax1.axvline(x=warmup_idx, color='black', linestyle='--', label=f'Warmup Point ({warmup_idx})')
    ax1.axhline(0, color='orange', lw=2)
    ax1.set_title("HFT-визуализация с детектором прогрева")
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(t, natr_slice, color='purple', label='NATR (%)')
    ax2.set_xlabel("Минутные бары")
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()
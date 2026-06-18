import os
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import windows

class MarketEngine:
    def __init__(self, gauss_base: int = 1260, natr_length: int = 840):
        self.gauss_base = gauss_base
        self.natr_length = natr_length
        self.kernels = self._generate_gaussian_kernels()
        print(f"Шаг 2.1: Ядра Гаусса сгенерированы (База: {gauss_base} сек, 5 слоев) -> [ОК]")
    
    def _generate_gaussian_kernels(self) -> list:
        kernels = []
        for i in range(5):
            sigma = self.gauss_base + (i * 60) 
            kernel = windows.gaussian(int(sigma * 6), std=sigma)
            kernel /= kernel.sum()
            kernels.append(kernel)
        return kernels
    
    def compute_gaussian_center(self, close: np.ndarray) -> np.ndarray:
        gauss_layers = []
        current = close.astype(float).copy()
        for kernel in self.kernels:
            smoothed = np.convolve(current, kernel, mode='same')
            gauss_layers.append(smoothed)
            current = smoothed  
        return np.nanmean(gauss_layers, axis=0)
    
    def run(self, df: pd.DataFrame) -> dict:
        print("Шаг 2.2: Запуск векторизованного расчёта массивов...")
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        gauss_center = self.compute_gaussian_center(close)
        
        tr = np.maximum(high - low, 
                        np.maximum(np.abs(high - np.roll(close, 1)), 
                                   np.abs(low - np.roll(close, 1))))
        atr = pd.Series(tr).rolling(self.natr_length).mean().values
        atr = np.nan_to_num(atr, nan=np.nanmean(atr))
        natr = atr / close * 100  
        
        return {
            'timestamp': df.index.values.astype(str),
            'open': df['open'].values,
            'high': high,
            'low': low,
            'close': close,
            'gauss_center': gauss_center,
            'natr': natr,
            'spread_multiplier': natr / 100.0,
            'reference_price': close * 1.0,
            'volume': df['volume'].values
        }
    
    def save_cache(self, market_state: dict, path: str = "cache/market_cache.npz"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, **market_state)
        print(f"[ФИНАЛ ЯЧЕЙКИ 2]: Кэш сохранён ({len(market_state['close']):,} сек) -> [ОК]")

if __name__ == "__main__":
    csv_path = '../data_collection/pepe_1s_data.csv'
    if os.path.exists(csv_path):
        print(f"Чтение файла данных: {csv_path}")
        df_raw = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        engine = MarketEngine()
        market_state = engine.run(df_raw)
        engine.save_cache(market_state)
    else:
        print(f"Критическая ошибка: Файл {csv_path} не найден. Помести csv в указанную директорию.")
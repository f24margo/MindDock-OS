import math
from collections import deque


def make_gaussian_get_orders(base_get_orders, gauss_window: int = 8, lag: int = 1):
    """
    Возвращает обёртку над base_get_orders с Gaussian-сглаживанием цены
    и lag-задержкой (моделирование latency реального бота).

    gauss_window: ширина окна сглаживания в тиках
    lag:          задержка в тиках (1 = предыдущий тик)
    """
    price_buffer = deque(maxlen=gauss_window)
    smoothed_buffer = deque(maxlen=lag + 1)
    weights = _gaussian_weights(gauss_window)

    def wrapped_get_orders(price, config, position):
        price_buffer.append(price)

        n = len(price_buffer)
        w = weights[-n:]
        w_sum = sum(w)
        smoothed_price = sum(p * wt for p, wt in zip(price_buffer, w)) / w_sum

        smoothed_buffer.append(smoothed_price)
        lagged_price = smoothed_buffer[0]

        return base_get_orders(lagged_price, config, position)

    wrapped_get_orders.__name__ = f"gaussian_lag{lag}_w{gauss_window}"
    wrapped_get_orders.__gauss_window__ = gauss_window
    wrapped_get_orders.__lag__ = lag

    return wrapped_get_orders


def _gaussian_weights(n: int) -> list:
    if n <= 1:
        return [1.0]
    sigma = n / 3.0
    center = n - 1
    weights = [math.exp(-0.5 * ((i - center) / sigma) ** 2) for i in range(n)]
    return weights

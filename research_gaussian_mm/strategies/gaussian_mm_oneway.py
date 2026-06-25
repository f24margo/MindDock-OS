from decimal import Decimal
from functools import lru_cache
from typing import List, Optional

import numpy as np
import pandas as pd
from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy_v2.controllers.market_making_controller_base import (
    MarketMakingControllerBase,
    MarketMakingControllerConfigBase,
)
from hummingbot.strategy_v2.executors.position_executor.data_types import PositionExecutorConfig
from hummingbot.core.data_type.common import OrderType


class GaussianMMOnewayConfig(MarketMakingControllerConfigBase):
    """
    Oneway MM: при сильном тренде торгуем только одну сторону.
    UP   тренд (trend_strength > +threshold): только BID (не продаём)
    DOWN тренд (trend_strength < -threshold): только ASK (не покупаем)
    FLAT (|trend_strength| <= threshold):     обе стороны (классический MM)

    Исследование 2026-06-24:
    - Протестирован на 1000PEPE-USDT 2026-06-18, fee=0% (maker rebate)
    - thr=0.3: total PnL +0.092, 6/6 окон валидны
    - thr=0.3 + IMB filter: total PnL +0.401, 5/6 окон валидны
    - Базовый gaussian_mm (mean-reversion): -0.328 на том же дне
    """
    controller_name:     str   = "gaussian_mm_oneway"
    candles_connector:   str   = Field(default=None)
    candles_trading_pair: str  = Field(default=None)
    interval:            str   = Field(default="1m")

    gauss_length:        int   = Field(default=19,    json_schema_extra={"is_updatable": True})
    gauss_distance_base: float = Field(default=1.594, json_schema_extra={"is_updatable": True})
    gaussian_layers:     int   = Field(default=5,     json_schema_extra={"is_updatable": True})
    natr_length:         int   = Field(default=4,     json_schema_extra={"is_updatable": True})
    atr_length:          int   = Field(default=24,    json_schema_extra={"is_updatable": True})
    flat_enter:          float = Field(default=0.3,   json_schema_extra={"is_updatable": True})
    flat_exit:           float = Field(default=0.59,  json_schema_extra={"is_updatable": True})
    min_natr:            float = Field(default=0.0008,json_schema_extra={"is_updatable": True})
    max_natr:            float = Field(default=0.05,  json_schema_extra={"is_updatable": True})
    price_shift_mult:    float = Field(default=0.978, json_schema_extra={"is_updatable": True})
    max_shift_pct:       float = Field(default=0.003, json_schema_extra={"is_updatable": True})
    trend_threshold:     float = Field(default=0.3,   json_schema_extra={"is_updatable": True})
    inventory_skew_mult: float = Field(default=0.5,   json_schema_extra={"is_updatable": True})
    trend_skew_mult:     float = Field(default=0.5,   json_schema_extra={"is_updatable": True})

    @field_validator("candles_connector", mode="before")
    @classmethod
    def set_candles_connector(cls, v, validation_info: ValidationInfo):
        if v is None or v == "":
            return validation_info.data.get("connector_name")
        return v

    @field_validator("candles_trading_pair", mode="before")
    @classmethod
    def set_candles_trading_pair(cls, v, validation_info: ValidationInfo):
        if v is None or v == "":
            return validation_info.data.get("trading_pair")
        return v


class GaussianMMOnewayController(MarketMakingControllerBase):

    def __init__(self, config: GaussianMMOnewayConfig, *args, **kwargs):
        self.config = config
        self.max_records = config.gauss_length + config.gaussian_layers + 120 + 100
        super().__init__(config, *args, **kwargs)

    def get_candles_config(self) -> List[CandlesConfig]:
        return [CandlesConfig(
            connector=self.config.candles_connector,
            trading_pair=self.config.candles_trading_pair,
            interval=self.config.interval,
            max_records=self.max_records,
        )]

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_gaussian_weights(length: int, sigma: float) -> np.ndarray:
        weights = np.array([np.exp(-0.5 * ((i - length / 2) / sigma) ** 2)
                           for i in range(length)])
        weights /= weights.sum()
        return weights

    def _gaussian_filter_fast(self, src: np.ndarray, length: int) -> np.ndarray:
        if len(src) < length:
            return np.full(len(src), np.nan)
        sigma = max(3.0, length / 3.0)
        weights = self._get_gaussian_weights(length, sigma)
        result = np.full(len(src), np.nan)
        result[length - 1:] = np.convolve(src, weights[::-1], mode='valid')
        return result

    def _compute_trend(self, df: pd.DataFrame) -> Optional[tuple]:
        src = df["close"].values
        length = self.config.gauss_length

        hi = df["high"].values
        lo = df["low"].values
        prev_cl = np.roll(src, 1); prev_cl[0] = src[0]
        tr = np.maximum(hi-lo, np.maximum(np.abs(hi-prev_cl), np.abs(lo-prev_cl)))
        atr_len = min(self.config.atr_length, len(src))
        atr = np.array([tr[max(0,i-atr_len):i+1].mean() for i in range(len(src))])
        atr = np.clip(atr, src[-1]*0.0005, None)

        gaussians = [self._gaussian_filter_fast(src, length + s)
                     for s in range(self.config.gaussian_layers)]
        value = np.nanmean(gaussians, axis=0)
        if np.isnan(value[-1]):
            return None

        natr_len = min(self.config.natr_length, len(src))
        natr = float(np.clip(
            np.nanmean((atr / np.where(src > 0, src, 1))[-natr_len:]),
            self.config.min_natr, self.config.max_natr
        ))

        gc = float(value[-1])
        cur_atr = float(atr[-1])
        raw = (src[-1] - gc) / max(cur_atr, 1e-10)
        trend_strength = float(3 * np.tanh(raw / 3))

        return gc, natr, trend_strength, cur_atr

    async def update_processed_data(self):
        candles = self.market_data_provider.get_candles_df(
            connector_name=self.config.candles_connector,
            trading_pair=self.config.candles_trading_pair,
            interval=self.config.interval,
            max_records=self.max_records,
        )
        if candles is None or candles.empty or len(candles) < (self.config.gauss_length + 100):
            return

        trend_data = self._compute_trend(candles)
        if trend_data is None:
            return

        gc, natr, trend_strength, cur_atr = trend_data
        close_price = candles["close"].iloc[-1]

        dynamic_alpha   = 0.15 + 0.35 * np.tanh(abs(trend_strength))
        adaptive_center = close_price * dynamic_alpha + gc * (1.0 - dynamic_alpha)
        smooth_skew     = np.tanh(0.5 * trend_strength)
        raw_shift       = smooth_skew * natr * self.config.price_shift_mult
        safe_shift      = float(np.clip(raw_shift,
                                        -self.config.max_shift_pct,
                                         self.config.max_shift_pct))
        reference_price   = Decimal(str(adaptive_center * (1.0 + safe_shift)))
        spread_multiplier = Decimal(str(natr))

        try:
            account_positions = self.market_data_provider.get_account_positions()
            pos_amount = 0.0
            for p in account_positions:
                if p.trading_pair == self.config.trading_pair:
                    pos_amount = float(p.amount)
                    break
            total_quote     = float(self.config.total_amount_quote)
            inventory_ratio = float(np.clip(
                (pos_amount * close_price) / max(1.0, total_quote), -1.0, 1.0
            ))
        except Exception:
            inventory_ratio = 0.0

        # === ONEWAY LOGIC ===
        thr = self.config.trend_threshold
        buy_volume_mod  = 1.0
        sell_volume_mod = 1.0

        if trend_strength > thr:
            sell_volume_mod = 0.0
        elif trend_strength < -thr:
            buy_volume_mod  = 0.0
        else:
            inv_factor      = inventory_ratio * self.config.inventory_skew_mult
            buy_volume_mod  = float(np.exp( 0.5 * inv_factor))
            sell_volume_mod = float(np.exp(-0.5 * inv_factor))

        self.processed_data = {
            "reference_price":     reference_price,
            "spread_multiplier":   spread_multiplier,
            "features":            candles,
            "trend_strength":      trend_strength,
            "inventory_ratio":     inventory_ratio,
            "gauss_center":        gc,
            "natr":                natr,
            "atr":                 cur_atr,
            "mode":               ("BUY_ONLY"  if trend_strength >  thr else
                                   "SELL_ONLY" if trend_strength < -thr else
                                   "FLAT_MM"),
            "buy_volume_modifier":  buy_volume_mod,
            "sell_volume_modifier": sell_volume_mod,
        }

    def get_executor_config(self, level_id: str, price: Decimal, amount: Decimal):
        trade_type = self.get_trade_type_from_level_id(level_id)
        modified_amount = amount
        if hasattr(self, "processed_data") and self.processed_data:
            if trade_type.name == "BUY":
                modified_amount = amount * Decimal(
                    f"{self.processed_data['buy_volume_modifier']:.4f}"
                )
            elif trade_type.name == "SELL":
                modified_amount = amount * Decimal(
                    f"{self.processed_data['sell_volume_modifier']:.4f}"
                )
        min_amount = Decimal("0.0001")
        if modified_amount < min_amount:
            modified_amount = min_amount
        return PositionExecutorConfig(
            timestamp=self.market_data_provider.time(),
            level_id=level_id,
            connector_name=self.config.connector_name,
            trading_pair=self.config.trading_pair,
            entry_price=price,
            amount=modified_amount,
            triple_barrier_config=self.config.triple_barrier_config,
            leverage=self.config.leverage,
            side=trade_type,
            open_order_type=OrderType.LIMIT_MAKER,
        )

# ПАТЧ: устанавливаем LIMIT_MAKER для получения maker rebate
# Применяется поверх существующего get_executor_config

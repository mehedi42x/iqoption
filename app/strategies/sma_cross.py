from app.schemas import BoardName, Candle, Side


class SMACrossStrategy:
    """Educational example only; emits BUY/SELL on a detected SMA crossover."""

    name = "sma_cross"
    fast_period = 5
    slow_period = 20

    def generate(self, board: BoardName, symbol: str, candles: list[Candle]) -> tuple[Side | None, str]:
        if len(candles) < self.slow_period + 1:
            return None, f"Need at least {self.slow_period + 1} candles; no trade signal."
        closes = [candle.close for candle in candles]
        previous_fast = sum(closes[-self.fast_period - 1:-1]) / self.fast_period
        previous_slow = sum(closes[-self.slow_period - 1:-1]) / self.slow_period
        current_fast = sum(closes[-self.fast_period:]) / self.fast_period
        current_slow = sum(closes[-self.slow_period:]) / self.slow_period
        if previous_fast <= previous_slow and current_fast > current_slow:
            return Side.BUY, f"{self.fast_period}-period SMA crossed above {self.slow_period}-period SMA."
        if previous_fast >= previous_slow and current_fast < current_slow:
            return Side.SELL, f"{self.fast_period}-period SMA crossed below {self.slow_period}-period SMA."
        return None, "No SMA crossover; no trade signal."

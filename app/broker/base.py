from typing import Protocol

from app.schemas import BoardName, Candle, Side, Trade


class Broker(Protocol):
    """Transport-neutral broker interface shared by every board."""

    def get_candles(self, symbol: str, interval_seconds: int, count: int) -> list[Candle]: ...

    def place_order(
        self,
        *,
        board: BoardName,
        symbol: str,
        side: Side,
        amount: float,
        duration_seconds: int,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        metadata: dict | None = None,
    ) -> Trade: ...

    def get_order(self, trade_id: str) -> Trade | None: ...

    def close_order(self, trade_id: str) -> Trade | None: ...

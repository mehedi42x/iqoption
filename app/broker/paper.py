from __future__ import annotations

import hashlib
import math
import time
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import BoardName, Candle, Side, Trade, TradeStatus


class PaperBroker:
    """Deterministic local market feed and simulated order lifecycle; no network calls."""

    def __init__(self) -> None:
        self._orders: dict[str, Trade] = {}

    def get_candles(self, symbol: str, interval_seconds: int = 60, count: int = 100) -> list[Candle]:
        if not 1 <= count <= 1000:
            raise ValueError("count must be between 1 and 1000")
        if interval_seconds < 1:
            raise ValueError("interval_seconds must be positive")
        digest = hashlib.sha256(symbol.upper().encode()).digest()
        seed = int.from_bytes(digest[:4], "big") / 2**32
        base = 1.0 + seed * 100.0
        now = int(time.time())
        candles: list[Candle] = []
        previous = base
        start = now - count * interval_seconds
        for index in range(count):
            wave = math.sin(index / 7.0 + seed * 20.0) * base * 0.002
            trend = index * base * 0.00001
            close = base + wave + trend
            open_price = previous
            wiggle = abs(math.sin(index * 1.73 + seed)) * base * 0.0003
            candles.append(Candle(
                timestamp=datetime.fromtimestamp(start + index * interval_seconds, tz=timezone.utc),
                open=open_price,
                high=max(open_price, close) + wiggle,
                low=min(open_price, close) - wiggle,
                close=close,
                volume=100.0 + (index % 19) * 3.0,
            ))
            previous = close
        return candles

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
    ) -> Trade:
        entry_price = self.get_candles(symbol, count=2)[-1].close
        trade = Trade(
            trade_id=str(uuid4()),
            board=board,
            symbol=symbol,
            side=side,
            amount=amount,
            duration_seconds=duration_seconds,
            status=TradeStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={**(metadata or {}), "execution": "paper"},
        )
        self._orders[trade.trade_id] = trade
        return trade

    def get_order(self, trade_id: str) -> Trade | None:
        return self._orders.get(trade_id)

    def close_order(self, trade_id: str) -> Trade | None:
        trade = self._orders.get(trade_id)
        if trade is None:
            return None
        if trade.status == TradeStatus.CLOSED:
            return trade
        exit_price = self.get_candles(trade.symbol, count=2)[-1].close
        closed = trade.model_copy(update={
            "status": TradeStatus.CLOSED,
            "closed_at": datetime.now(timezone.utc),
            "exit_price": exit_price,
        })
        self._orders[trade_id] = closed
        return closed

    def restore_order(self, trade: Trade) -> None:
        """Restore persisted local state after a server restart."""
        self._orders.setdefault(trade.trade_id, trade)

    def update_risk(self, trade_id: str, stop_loss: float | None, take_profit: float | None) -> Trade | None:
        trade = self._orders.get(trade_id)
        if trade is None:
            return None
        updated = trade.model_copy(update={"stop_loss": stop_loss, "take_profit": take_profit})
        self._orders[trade_id] = updated
        return updated

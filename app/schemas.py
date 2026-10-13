from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoardName(StrEnum):
    TURBO = "turbo"
    OPTION = "option"
    BINARY = "binary"
    MARGIN = "margin"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class Signal(BaseModel):
    board: BoardName
    symbol: str
    side: Side | None = None
    strategy: str
    rationale: str
    generated_at: datetime


class TradeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9._/-]+$")
    side: Side
    amount: float = Field(gt=0)
    duration_seconds: int | None = Field(default=None, ge=1, le=86_400)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_at_least_one_level(self):
        if not self.model_fields_set.intersection({"stop_loss", "take_profit"}):
            raise ValueError("Provide stop_loss, take_profit, or both.")
        return self


class Trade(BaseModel):
    trade_id: str
    board: BoardName
    symbol: str
    side: Side
    amount: float
    duration_seconds: int
    status: TradeStatus = TradeStatus.OPEN
    opened_at: datetime
    closed_at: datetime | None = None
    entry_price: float
    exit_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CloseTradeResponse(BaseModel):
    trade: Trade
    message: str

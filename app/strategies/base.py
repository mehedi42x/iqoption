from typing import Protocol

from app.schemas import BoardName, Candle, Side


class Strategy(Protocol):
    name: str

    def generate(self, board: BoardName, symbol: str, candles: list[Candle]) -> tuple[Side | None, str]: ...

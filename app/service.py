from __future__ import annotations

from datetime import datetime, timezone

from app.broker.iqoption import IQOptionBroker, IQOptionIntegrationUnavailable
from app.broker.paper import PaperBroker
from app.repository import TradeRepository
from app.schemas import BoardName, RiskUpdateRequest, Signal, Trade, TradeRequest, TradeStatus
from app.settings import Settings, get_settings
from app.strategies.loader import load_strategy


class TradingDisabledError(RuntimeError):
    pass


class RiskLimitError(ValueError):
    pass


class TradingService:
    """One shared business-logic layer for all independent board routers."""

    def __init__(self, settings: Settings | None = None, broker=None, repository: TradeRepository | None = None):
        self.settings = settings or get_settings()
        if self.settings.account_mode == "real":
            raise IQOptionIntegrationUnavailable(
                "Real account mode is selected, but no secure, supported IQ Option adapter is configured. "
                "Live orders are disabled; select ACCOUNT_MODE=demo to use the local simulator."
            )
        self.broker = broker or self._make_broker()
        self.settings.ensure_database_parent()
        self.repository = repository or TradeRepository(self.settings.database_path)
        self.strategy = load_strategy(self.settings.strategy_name)

    def _make_broker(self):
        if self.settings.account_mode == "real":
            raise IQOptionIntegrationUnavailable(
                "Real account mode is selected, but no secure, supported IQ Option adapter is configured. "
                "Live orders are disabled; select ACCOUNT_MODE=demo to use the local simulator."
            )
        if self.settings.broker_mode == "paper":
            return PaperBroker()
        return IQOptionBroker(self.settings.iq_option_email, self.settings.iq_option_password)

    def get_candles(self, board: BoardName, symbol: str, count: int = 100):
        return self.broker.get_candles(symbol, self.settings.market_data_interval_seconds, count)

    def get_signal(self, board: BoardName, symbol: str) -> Signal:
        candles = self.get_candles(board, symbol, count=100)
        side, rationale = self.strategy.generate(board, symbol, candles)
        return Signal(
            board=board,
            symbol=symbol,
            side=side,
            strategy=self.strategy.name,
            rationale=rationale,
            generated_at=datetime.now(timezone.utc),
        )

    def create_trade(self, board: BoardName, request: TradeRequest) -> Trade:
        if not self.settings.trading_enabled:
            raise TradingDisabledError("Trading is disabled; set TRADING_ENABLED=true for the local demo simulator.")
        if request.amount > self.settings.max_stake:
            raise RiskLimitError(f"amount exceeds MAX_STAKE ({self.settings.max_stake}).")
        if board != BoardName.MARGIN and (request.stop_loss is not None or request.take_profit is not None):
            raise ValueError("stop_loss and take_profit are accepted only on the margin board.")
        duration = request.duration_seconds or self.settings.duration_for(board.value)
        trade = self.broker.place_order(
            board=board,
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            duration_seconds=duration,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            metadata=request.metadata,
        )
        return self.repository.save(trade)

    def get_trade(self, trade_id: str) -> Trade | None:
        return self.repository.get(trade_id)

    def list_trades(self, board: BoardName | None = None, status: TradeStatus | None = None) -> list[Trade]:
        return self.repository.list(board=board, status=status)

    def delete_trade(self, trade_id: str) -> bool:
        return self.repository.delete(trade_id)

    def close_trade(self, trade_id: str) -> Trade | None:
        stored = self.repository.get(trade_id)
        if stored is None:
            return None
        if stored.status == TradeStatus.CLOSED:
            return stored
        if hasattr(self.broker, "restore_order"):
            self.broker.restore_order(stored)
        closed = self.broker.close_order(trade_id)
        if closed is not None:
            return self.repository.save(closed)
        return None

    def set_margin_risk(self, trade_id: str, request: RiskUpdateRequest) -> Trade | None:
        stored = self.repository.get(trade_id)
        if stored is None:
            return None
        if stored.board != BoardName.MARGIN:
            raise ValueError("Stop-loss/take-profit updates are available only on the margin board.")
        if stored.status != TradeStatus.OPEN:
            raise ValueError("Risk levels can only be changed on an open paper trade.")
        changes = request.model_dump(exclude_unset=True)
        updated = stored.model_copy(update=changes)
        if hasattr(self.broker, "update_risk"):
            self.broker.update_risk(trade_id, updated.stop_loss, updated.take_profit)
        return self.repository.save(updated)

    def automated_tick(self) -> list[Trade]:
        if not self.settings.trading_enabled:
            return []
        board = BoardName(self.settings.trade_type)
        signal = self.get_signal(board, self.settings.strategy_symbol)
        if signal.side is None:
            return []
        trade = self.create_trade(board, TradeRequest(
            symbol=signal.symbol,
            side=signal.side,
            amount=min(1.0, self.settings.max_stake),
            duration_seconds=self.settings.duration_for(board.value),
            metadata={"strategy": signal.strategy, "rationale": signal.rationale, "automation": True},
        ))
        return [trade]

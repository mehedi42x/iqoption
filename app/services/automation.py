import asyncio
import logging

from app.service import TradingService

logger = logging.getLogger(__name__)


class AutomationNotAllowed(RuntimeError):
    pass


class AutomationController:
    def __init__(self, service: TradingService) -> None:
        self.service = service
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> dict[str, object]:
        settings = self.service.settings
        if settings.account_mode != "demo" or settings.broker_mode != "paper":
            raise AutomationNotAllowed("Automation is supported only in demo mode using the local simulator.")
        if not settings.trading_enabled or not settings.auto_trading_enabled:
            raise AutomationNotAllowed(
                "Automation is disabled. Set both TRADING_ENABLED=true and AUTO_TRADING_ENABLED=true for demo mode."
            )
        if not self.running:
            self._task = asyncio.create_task(self._loop(), name="paper-trading-automation")
        return self.status()

    async def stop(self) -> dict[str, object]:
        if self.running and self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        return self.status()

    def status(self) -> dict[str, object]:
        return {
            "running": self.running,
            "account_mode": self.service.settings.account_mode,
            "broker_mode": self.service.settings.broker_mode,
            "trade_type": self.service.settings.trade_type,
            "symbol": self.service.settings.strategy_symbol,
            "trading_enabled": self.service.settings.trading_enabled,
            "auto_trading_enabled": self.service.settings.auto_trading_enabled,
            "interval_seconds": self.service.settings.auto_interval_seconds,
        }

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self.service.automated_tick)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # Keep long-running automation alive without logging secrets.
                logger.warning("Paper automation tick failed (%s).", type(exc).__name__)
            await asyncio.sleep(self.service.settings.auto_interval_seconds)

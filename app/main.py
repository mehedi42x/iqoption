from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from app.boards.binary import router as binary_router
from app.boards.margin import router as margin_router
from app.boards.option import router as option_router
from app.boards.turbo import router as turbo_router
from app.dependencies import get_service
from app.schemas import BoardName, CloseTradeResponse, RiskUpdateRequest, Trade, TradeStatus
from app.service import TradingService
from app.services.automation import AutomationController, AutomationNotAllowed
from app.settings import Settings, get_settings


def create_app(settings: Settings | None = None, broker=None, repository=None) -> FastAPI:
    config = settings or get_settings()
    config.ensure_database_parent()
    service = TradingService(settings=config, broker=broker, repository=repository)
    automation = AutomationController(service)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        await automation.stop()

    application = FastAPI(title=config.app_name, version="0.1.0", lifespan=lifespan)
    application.state.service = service
    application.state.automation = automation
    prefix = "/api/v1"
    application.include_router(turbo_router, prefix=f"{prefix}/boards/turbo", tags=["turbo"])
    application.include_router(option_router, prefix=f"{prefix}/boards/option", tags=["option"])
    application.include_router(binary_router, prefix=f"{prefix}/boards/binary", tags=["binary"])
    application.include_router(margin_router, prefix=f"{prefix}/boards/margin", tags=["margin"])

    @application.get(f"{prefix}/health")
    def health():
        return {
            "status": "ok",
            "account_mode": config.account_mode,
            "broker_mode": config.broker_mode,
            "trade_type": config.trade_type,
            "symbol": config.strategy_symbol,
            "live_broker_available": False,
        }

    @application.get(f"{prefix}/config")
    def public_config():
        """Return non-secret runtime selections; credentials are never exposed."""
        return {
            "account_mode": config.account_mode,
            "broker_mode": config.broker_mode,
            "trade_type": config.trade_type,
            "symbol": config.strategy_symbol,
            "trading_enabled": config.trading_enabled,
            "auto_trading_enabled": config.auto_trading_enabled,
            "supported_trade_types": [board.value for board in BoardName],
            "live_broker_available": False,
        }

    @application.get(f"{prefix}/boards")
    def boards():
        return [{"name": board.value, "duration_seconds": config.duration_for(board.value)} for board in BoardName]

    @application.get(f"{prefix}/trades", response_model=list[Trade])
    def list_trades(board: BoardName | None = None, status: TradeStatus | None = None,
                    service: TradingService = Depends(get_service)):
        return service.list_trades(board=board, status=status)

    @application.get(f"{prefix}/trades/{{trade_id}}", response_model=Trade)
    def get_trade(trade_id: str, service: TradingService = Depends(get_service)):
        trade = service.get_trade(trade_id)
        if trade is None:
            raise HTTPException(status_code=404, detail="Trade not found")
        return trade

    @application.delete(f"{prefix}/trades/{{trade_id}}", status_code=204)
    def delete_trade(trade_id: str, service: TradingService = Depends(get_service)):
        if not service.delete_trade(trade_id):
            raise HTTPException(status_code=404, detail="Trade not found")
        return None

    @application.post(f"{prefix}/trades/{{trade_id}}/close", response_model=CloseTradeResponse)
    def close_trade(trade_id: str, service: TradingService = Depends(get_service)):
        trade = service.close_trade(trade_id)
        if trade is None:
            raise HTTPException(status_code=404, detail="Trade not found or could not be closed")
        return CloseTradeResponse(trade=trade, message="Paper trade closed.")

    @application.put(f"{prefix}/trades/{{trade_id}}/risk", response_model=Trade)
    def set_trade_risk(trade_id: str, request: RiskUpdateRequest,
                       service: TradingService = Depends(get_service)):
        try:
            trade = service.set_margin_risk(trade_id, request)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if trade is None:
            raise HTTPException(status_code=404, detail="Trade not found")
        return trade

    @application.get(f"{prefix}/automation/status")
    def automation_status():
        return automation.status()

    @application.post(f"{prefix}/automation/start")
    async def automation_start():
        try:
            return await automation.start()
        except AutomationNotAllowed as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @application.post(f"{prefix}/automation/stop")
    async def automation_stop():
        return await automation.stop()

    return application


app = create_app()

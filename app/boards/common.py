from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_service
from app.schemas import BoardName, CloseTradeResponse, Signal, Trade, TradeRequest
from app.service import RiskLimitError, TradingDisabledError, TradingService


def build_board_router(board: BoardName) -> APIRouter:
    router = APIRouter()

    @router.get("/candles")
    def candles(
        symbol: str = Query(min_length=1, max_length=40),
        count: int = Query(default=100, ge=1, le=1000),
        service: TradingService = Depends(get_service),
    ):
        try:
            return service.get_candles(board, symbol, count)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.post("/signal", response_model=Signal)
    def signal(
        symbol: str = Query(min_length=1, max_length=40),
        service: TradingService = Depends(get_service),
    ):
        return service.get_signal(board, symbol)

    @router.post("/trades", response_model=Trade, status_code=201)
    def create_trade(request: TradeRequest, service: TradingService = Depends(get_service)):
        try:
            return service.create_trade(board, request)
        except TradingDisabledError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except RiskLimitError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router

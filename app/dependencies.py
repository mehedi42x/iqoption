from fastapi import Request

from app.service import TradingService


def get_service(request: Request) -> TradingService:
    return request.app.state.service

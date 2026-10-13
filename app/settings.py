from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    app_name: str = "IQ Option Modular Automation API"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    account_mode: Literal["demo", "real"] = "demo"
    broker_mode: Literal["paper", "iqoption"] = "paper"
    trade_type: Literal["turbo", "option", "binary", "margin"] = "binary"
    trading_enabled: bool = False
    auto_trading_enabled: bool = False
    max_stake: float = Field(default=1.0, gt=0)
    default_duration_seconds: int = Field(default=60, ge=1)
    market_data_interval_seconds: int = Field(default=60, ge=1)
    turbo_duration_seconds: int = Field(default=60, ge=1)
    option_duration_seconds: int = Field(default=60, ge=1)
    binary_duration_seconds: int = Field(default=60, ge=1)
    margin_duration_seconds: int = Field(default=60, ge=1)
    auto_interval_seconds: int = Field(default=60, ge=5)
    strategy_name: str = "sma_cross"
    strategy_symbol: str = Field(default="EURUSD", min_length=1, max_length=40, pattern=r"^[A-Za-z0-9._/-]+$")
    database_path: str = "data/trades.sqlite3"
    iq_option_email: str = ""
    iq_option_password: str = ""

    def duration_for(self, board: str) -> int:
        return {
            "turbo": self.turbo_duration_seconds,
            "option": self.option_duration_seconds,
            "binary": self.binary_duration_seconds,
            "margin": self.margin_duration_seconds,
        }[board]

    def ensure_database_parent(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

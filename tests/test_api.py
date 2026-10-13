from fastapi.testclient import TestClient

from app.broker.iqoption import IQOptionIntegrationUnavailable
from app.main import create_app
from app.schemas import BoardName
from app.settings import Settings


def make_app(tmp_path, **overrides):
    defaults = {
        "_env_file": None,
        "broker_mode": "paper",
        "trading_enabled": False,
        "auto_trading_enabled": False,
        "database_path": str(tmp_path / "trades.sqlite3"),
        "max_stake": 2.0,
    }
    defaults.update(overrides)
    return create_app(Settings(**defaults))


def test_health_and_separate_boards(tmp_path):
    client = TestClient(make_app(tmp_path))
    assert client.get("/api/v1/health").json()["live_broker_available"] is False
    board_names = {item["name"] for item in client.get("/api/v1/boards").json()}
    assert board_names == {board.value for board in BoardName}
    for board in board_names:
        response = client.get(f"/api/v1/boards/{board}/candles", params={"symbol": "EURUSD", "count": 30})
        assert response.status_code == 200
        assert len(response.json()) == 30
        signal = client.post(f"/api/v1/boards/{board}/signal", params={"symbol": "EURUSD"})
        assert signal.status_code == 200
        assert signal.json()["side"] in {"buy", "sell", None}


def test_config_selects_demo_pair_and_supported_trade_type(tmp_path):
    client = TestClient(make_app(
        tmp_path,
        account_mode="demo",
        trading_enabled=True,
        trade_type="turbo",
        strategy_symbol="USD/JPY-OTC",
    ))
    config = client.get("/api/v1/config").json()
    assert config["account_mode"] == "demo"
    assert config["trade_type"] == "turbo"
    assert config["symbol"] == "USD/JPY-OTC"
    assert set(config["supported_trade_types"]) == {"turbo", "option", "binary", "margin"}
    assert "iq_option_password" not in config

    trade = client.post("/api/v1/boards/binary/trades", json={
        "symbol": "USD/JPY-OTC", "side": "buy", "amount": 1.0,
    })
    assert trade.status_code == 201
    assert trade.json()["symbol"] == "USD/JPY-OTC"


def test_trade_gate_tracking_and_close(tmp_path):
    client = TestClient(make_app(tmp_path, trading_enabled=True))
    payload = {"symbol": "EURUSD", "side": "buy", "amount": 1.0}
    created = client.post("/api/v1/boards/turbo/trades", json=payload)
    assert created.status_code == 201
    trade = created.json()
    assert trade["board"] == "turbo"
    assert trade["status"] == "open"
    closed = client.post(f"/api/v1/trades/{trade['trade_id']}/close")
    assert closed.status_code == 200
    assert closed.json()["trade"]["status"] == "closed"
    assert client.get("/api/v1/trades", params={"status": "closed"}).json()[0]["trade_id"] == trade["trade_id"]


def test_trading_disabled_by_default(tmp_path):
    client = TestClient(make_app(tmp_path))
    response = client.post("/api/v1/boards/binary/trades", json={"symbol": "EURUSD", "side": "sell", "amount": 1})
    assert response.status_code == 403


def test_risk_limit_and_margin_stops(tmp_path):
    client = TestClient(make_app(tmp_path, trading_enabled=True, max_stake=1.0))
    over_limit = client.post("/api/v1/boards/option/trades", json={"symbol": "EURUSD", "side": "buy", "amount": 2})
    assert over_limit.status_code == 422
    margin = client.post("/api/v1/boards/margin/trades", json={
        "symbol": "EURUSD", "side": "sell", "amount": 1,
        "stop_loss": 1.1, "take_profit": 1.0,
    })
    assert margin.status_code == 201
    non_margin = client.post("/api/v1/boards/turbo/trades", json={
        "symbol": "EURUSD", "side": "buy", "amount": 1, "stop_loss": 1.1,
    })
    assert non_margin.status_code == 422


def test_live_broker_mode_fails_closed(tmp_path):
    settings = Settings(
        _env_file=None,
        account_mode="real",
        broker_mode="paper",
        database_path=str(tmp_path / "trades.sqlite3"),
    )
    try:
        create_app(settings)
    except IQOptionIntegrationUnavailable as exc:
        assert "secure, supported" in str(exc)
    else:
        raise AssertionError("Live broker mode must fail closed")


def test_automation_gated(tmp_path):
    client = TestClient(make_app(tmp_path))
    assert client.post("/api/v1/automation/start").status_code == 403


def test_margin_risk_update_only_on_open_margin_trade(tmp_path):
    client = TestClient(make_app(tmp_path, trading_enabled=True))
    margin = client.post("/api/v1/boards/margin/trades", json={"symbol": "EURUSD", "side": "buy", "amount": 1})
    assert margin.status_code == 201
    trade_id = margin.json()["trade_id"]
    changed = client.put(f"/api/v1/trades/{trade_id}/risk", json={"stop_loss": 1.01, "take_profit": 1.2})
    assert changed.status_code == 200
    assert changed.json()["stop_loss"] == 1.01
    assert changed.json()["take_profit"] == 1.2
    closed = client.post(f"/api/v1/trades/{trade_id}/close")
    assert closed.status_code == 200
    assert client.put(f"/api/v1/trades/{trade_id}/risk", json={"stop_loss": 1.0}).status_code == 422

    turbo = client.post("/api/v1/boards/turbo/trades", json={"symbol": "EURUSD", "side": "sell", "amount": 1})
    assert turbo.status_code == 201
    assert client.put(f"/api/v1/trades/{turbo.json()['trade_id']}/risk", json={"take_profit": 1.3}).status_code == 422

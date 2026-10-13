# IQ Option Modular Automation API (safe scaffold)

A Python/FastAPI scaffold with four independent trade boards (`turbo`, `option`, `binary`, `margin`), one shared service layer, pluggable strategies, a local simulator, trade tracking, and configurable board durations.

> **Important:** Selecting `ACCOUNT_MODE=demo` currently uses a local paper simulator; it does not log in to an IQ Option demo wallet or use live market data. Selecting `ACCOUNT_MODE=real` intentionally prevents the app from starting because this project has no secure, supported IQ Option broker adapter. A config switch alone does not make live trading operational or safe. Do not treat this scaffold as investment advice or a profitable strategy.

## Features

- Separate board routers: `/api/v1/boards/turbo`, `/option`, `/binary`, `/margin`.
- Shared order, storage, mock market-data, and strategy services.
- `DELETE /api/v1/trades/{trade_id}` permanently removes only that trade's SQLite row and its stored values; unrelated rows remain, and a later creation starts with a fresh row.
- Four currently supported trade types: `turbo`, `option`, `binary`, and `margin`.
- Configure the strategy symbol freely (subject to the app's symbol-character validation); there is no built-in currency-pair allowlist. The simulator generates synthetic candles for any accepted symbol—it does not confirm that the symbol exists at IQ Option.
- Choose `ACCOUNT_MODE=demo` or `ACCOUNT_MODE=real` in `.env`. Demo means local simulation only. Real mode fails closed until a secure supported adapter is implemented and reviewed.
- Choose the automation board with `TRADE_TYPE`; automation trades only that one configured board and uses `STRATEGY_SYMBOL`.
- `.env` controls trading and automation gates, stake limits, durations, and local SQLite storage.
- Tests never call IQ Option or place broker orders.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
# Keep ACCOUNT_MODE=demo and BROKER_MODE=paper. Keep both trading gates false until ready.
python -m app
```

Open `http://127.0.0.1:8000/docs` for the API explorer. The service binds to localhost by default; do not expose it to a public network without adding authentication and reviewing deployment security.

## Configuration

`.env.example` is a template. Copy it to `.env`; `.env` is gitignored and must stay on your machine. IQ Option credential fields are blank placeholders and are not consumed. Never commit real credentials, tokens, account IDs, logs, or database files.

```dotenv
ACCOUNT_MODE=demo                 # demo or real; real intentionally fails closed
BROKER_MODE=paper                 # local simulator only
TRADE_TYPE=binary                # turbo, option, binary, or margin
STRATEGY_SYMBOL=EURUSD            # e.g. USD/JPY-OTC; no pair allowlist
TRADING_ENABLED=false
AUTO_TRADING_ENABLED=false
MAX_STAKE=1.00
```

`GET /api/v1/config` shows the active non-secret selections and supported trade types. It never returns broker credentials. For manual API trades, the board in the route selects the trade type and the request's `symbol` selects the instrument. For automated strategy runs, `TRADE_TYPE` and `STRATEGY_SYMBOL` select one board and symbol.

- `ACCOUNT_MODE=demo` + `BROKER_MODE=paper` uses the local simulator. It is not an authenticated IQ Option demo account.
- `ACCOUNT_MODE=real` fails during application startup with a clear error. It cannot send real orders.
- `TRADING_ENABLED=false` and `AUTO_TRADING_ENABLED=false` by default. Both must be explicitly enabled for demo automation.
- `TURBO_DURATION_SECONDS`, `OPTION_DURATION_SECONDS`, `BINARY_DURATION_SECONDS`, and `MARGIN_DURATION_SECONDS` configure durations.
- `MAX_STAKE` caps simulated orders.

## API overview

- `GET /api/v1/health`, `GET /api/v1/config`, `GET /api/v1/boards`
- For each board, `GET /api/v1/boards/{board}/candles`, `POST /api/v1/boards/{board}/signal`, and `POST /api/v1/boards/{board}/trades`.
- `GET /api/v1/trades`, `GET /api/v1/trades/{trade_id}`, `DELETE /api/v1/trades/{trade_id}` (permanently removes the database entry), `POST /api/v1/trades/{trade_id}/close`, `PUT /api/v1/trades/{trade_id}/risk` (margin board only).
- `GET /api/v1/automation/status`, `POST /api/v1/automation/start`, `POST /api/v1/automation/stop`.

The API accepts `buy`/`sell`. The community docs describe binary/turbo calls as call/put; mapping this scaffold to any future official broker SDK must be explicitly reviewed rather than assumed.

## Tests

```bash
python -m pytest
```

All tests use the local simulator and deterministic candles. They do not need `.env`, network access, saved broker credentials, or a broker account.

## Integration status and references

- Community Python client README: <https://github.com/iqoptionapi/iqoptionapi> (calls itself unofficial and warns against using a real account).
- The previously inspected community client source disables TLS verification, so it is intentionally excluded.
- Community documentation lists distinct order/data operations for binary/digital and forex/futures, including stop-loss/take-profit fields for some products. That does not establish a broker-supported or secure API; this scaffold makes no live capability guarantee.

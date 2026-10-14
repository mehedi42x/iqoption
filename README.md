# IQ Option Modular Automation API (safe scaffold)

A Python/FastAPI scaffold with four independent trade boards (`turbo`, `option`, `binary`, `margin`), one shared service layer, pluggable strategies, a local simulator, trade tracking, and configurable board durations.

> **Important:** Selecting `ACCOUNT_MODE=demo` currently uses a local paper simulator; it does not log in to an IQ Option demo wallet or use live market data. Selecting `ACCOUNT_MODE=real` intentionally prevents the app from starting because this project has no secure, supported IQ Option broker adapter. A config switch alone does not make live trading operational or safe. Do not treat this scaffold as investment advice or a profitable strategy.

## Features

- Separate board routers: `/api/v1/boards/turbo`, `/option`, `/binary`, `/margin`.
- Shared order, storage, mock market-data, and strategy services.
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

## Termux (Android)

Install Termux from [F-Droid](https://f-droid.org/packages/com.termux/) or the [official GitHub releases](https://github.com/termux/termux-app/releases). In Termux:

```sh
pkg update && pkg upgrade -y
pkg install -y git
git clone https://github.com/mehedi42x/iqoption.git
cd iqoption
bash scripts/termux-setup.sh
cp .env.example .env
. .venv/bin/activate
python -m app
```

Open `http://127.0.0.1:8000/docs` in a browser on the same phone. Keep the default loopback host; do not expose this unauthenticated API to the internet. Stop the server with `Ctrl+C`. To install test tools as well, run `bash scripts/termux-setup.sh --with-dev`, then `. .venv/bin/activate` and `python -m pytest`.

The setup script installs Termux Python and the Rust/native build tools needed if a dependency such as `pydantic-core` has to build from source on Android. That build may take time and is device-dependent. The project requires Python 3.11 or newer; the Termux package version can change, so check `python --version` if installation fails. Dependencies remain declared in `pyproject.toml`; the script installs into a project-local virtual environment and does not change Termux's system Python packages.

## Configuration

`.env.example` is a template. Copy it to `.env`; `.env` is gitignored and must stay on your machine. IQ Option credential fields are blank placeholders and are not consumed. Never commit real credentials, tokens, account IDs, logs, or database files.

```dotenv
ACCOUNT_MODE=demo                 # demo or real; real intentionally fails closed
BROKER_MODE=paper                 # local simulator only
TRADE_TYPE=binary                 # turbo, option, binary, or margin
STRATEGY_SYMBOL=EURUSD             # e.g. USD/JPY-OTC; no pair allowlist
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
- `GET /api/v1/trades`, `GET /api/v1/trades/{trade_id}`, `POST /api/v1/trades/{trade_id}/close`, `PUT /api/v1/trades/{trade_id}/risk` (margin board only).
- `GET /api/v1/automation/status`, `POST /api/v1/automation/start`, `POST /api/v1/automation/stop`.

The API accepts `buy`/`sell`. The community docs describe binary/turbo calls as call/put; mapping this scaffold to any future official broker SDK must be explicitly reviewed rather than assumed.

## Currency-pair input and IDs

Use the pair text directly, for example `EURUSD`, `EUR/USD`, or `USD/JPY-OTC`; no numeric ID is needed by this project's paper simulator. The same `symbol` field selects the symbol for candles, signals, manual paper trades, and the configured automation strategy. A regression test covers passing a pair string without an ID. This is **not** a broker market lookup: paper candles are synthetic, and the app does not verify that a pair exists or is currently tradable at IQ Option. There is deliberately no hardcoded IQ Option asset-ID table—the project has no verified broker adapter or live asset catalog, and stale/product-specific IDs must not be presented as verified or used to place orders.

## WebSocket status

This repository currently contains no WebSocket client, server route, broker endpoint, or WebSocket protocol/subprotocol configuration. Therefore there is no IQ Option WebSocket connection to test, and this update does not claim that any broker WebSocket protocol works. RFC 6455 defines the WebSocket transport; application subprotocols are endpoint-specific, not a universal list that can be tested without a specified server. Uvicorn's optional `standard` extras were removed because this HTTP-only scaffold does not use them and their extra native dependencies are unnecessary for Termux.

## Tests

```bash
python -m pytest
```

All tests use the local simulator and deterministic candles. They do not need `.env`, network access, saved broker credentials, or a broker account.

## Integration status and references

- Termux Python installation uses `pkg install python`; see the [Termux Python guide](https://wiki.termux.com/wiki/Python) and [Termux app installation notes](https://github.com/termux/termux-app).
- Uvicorn documents its minimal install and optional `standard` dependencies on [PyPI](https://pypi.org/project/uvicorn/).
- WebSocket transport and endpoint-selected subprotocol behavior are specified in [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html).
- Community Python client README: <https://github.com/iqoptionapi/iqoptionapi> (calls itself unofficial and warns against using a real account).
- The previously inspected community client source disables TLS verification, so it is intentionally excluded.
- Community documentation lists distinct order/data operations for binary/digital and forex/futures, including stop-loss/take-profit fields for some products. That does not establish a broker-supported or secure API; this scaffold makes no live capability guarantee.

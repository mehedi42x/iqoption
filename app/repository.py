import sqlite3
from pathlib import Path

from app.schemas import BoardName, Trade, TradeStatus


class TradeRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS trades (trade_id TEXT PRIMARY KEY, board TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_trades_board_status ON trades(board, status)")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def save(self, trade: Trade) -> Trade:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO trades(trade_id, board, status, payload) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(trade_id) DO UPDATE SET board=excluded.board, status=excluded.status, payload=excluded.payload",
                (trade.trade_id, trade.board.value, trade.status.value, trade.model_dump_json()),
            )
        return trade

    def get(self, trade_id: str) -> Trade | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM trades WHERE trade_id = ?", (trade_id,)).fetchone()
        return Trade.model_validate_json(row["payload"]) if row else None

    def list(self, board: BoardName | None = None, status: TradeStatus | None = None) -> list[Trade]:
        query = "SELECT payload FROM trades WHERE 1=1"
        params: list[str] = []
        if board is not None:
            query += " AND board = ?"
            params.append(board.value)
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY rowid DESC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [Trade.model_validate_json(row["payload"]) for row in rows]

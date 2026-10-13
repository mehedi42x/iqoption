from app.boards.common import build_board_router
from app.schemas import BoardName

router = build_board_router(BoardName.BINARY)

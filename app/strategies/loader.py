from app.strategies.base import Strategy
from app.strategies.sma_cross import SMACrossStrategy


_STRATEGIES: dict[str, type[Strategy]] = {
    "sma_cross": SMACrossStrategy,
}


def load_strategy(name: str) -> Strategy:
    try:
        strategy_type = _STRATEGIES[name.strip().lower()]
    except KeyError as exc:
        available = ", ".join(sorted(_STRATEGIES))
        raise ValueError(f"Unknown strategy {name!r}; registered strategies: {available}") from exc
    return strategy_type()


def available_strategies() -> list[str]:
    return sorted(_STRATEGIES)

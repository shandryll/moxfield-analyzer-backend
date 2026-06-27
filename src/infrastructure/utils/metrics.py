import time
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar
from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


def measure_time(
    func: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> R:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "Request completed",
                function=func.__name__,
                duration_ms=round(duration_ms, 2),
            )
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Request failed",
                function=func.__name__,
                duration_ms=round(duration_ms, 2),
                error=str(e),
            )
            raise

    return async_wrapper

import asyncio
import os
import sys
import pytest
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

os.environ["ENVIRONMENT"] = "test"
os.environ["CACHE_DECK_TTL"] = "300"
os.environ["CACHE_ORACLE_TTL"] = "3600"
os.environ["BROWSER_POOL_MAX_USES"] = "50"
os.environ["LOG_LEVEL"] = "ERROR"


@pytest.fixture(autouse=True)
def _reset_global_state():
    from src.infrastructure.http.rate_limit import limiter
    from src.infrastructure.utils.cache import deck_cache, oracle_cache, combo_cache

    limiter._storage.reset()
    deck_cache.clear()
    oracle_cache.clear()
    combo_cache.clear()

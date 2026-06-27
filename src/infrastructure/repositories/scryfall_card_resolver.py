import asyncio
import os
import httpx
from loguru import logger
from src.infrastructure.utils.cache import oracle_cache
from src.infrastructure.utils.http_client import get_http_client

SCRYFALL_API_BASE = os.getenv("SCRYFALL_API_BASE_URL", "https://api.scryfall.com")
MAX_RETRIES = int(os.getenv("SCRYFALL_MAX_RETRIES", "2"))
TIMEOUT = float(os.getenv("SCRYFALL_TIMEOUT_SECONDS", "5"))


class ScryfallCardResolver:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or get_http_client(timeout=TIMEOUT)

    async def resolve(self, scryfall_ids: list[str]) -> dict[str, str]:
        unique = list(set(scryfall_ids))
        cached_count = sum(1 for sid in unique if sid in oracle_cache)
        
        if cached_count > 0:
            logger.info(
                "Resolving oracle IDs",
                total=len(unique),
                cached=cached_count,
                to_fetch=len(unique) - cached_count,
            )

        results = await asyncio.gather(*[self._fetch_one(sid) for sid in unique])
        mapping: dict[str, str] = {}
        for sid, oid in zip(unique, results):
            if oid:
                mapping[sid] = oid

        logger.info(
            "Oracle ID resolution completed",
            requested=len(unique),
            resolved=len(mapping),
            failed=len(unique) - len(mapping),
        )
        return mapping

    async def _fetch_one(self, scryfall_id: str) -> str | None:
        cached = oracle_cache.get(scryfall_id)
        if cached:
            return cached

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                res = await self._client.get(
                    f"{SCRYFALL_API_BASE}/cards/{scryfall_id}",
                )
                data = res.json()
                oracle_id = data.get("oracle_id")
                if oracle_id:
                    oracle_cache[scryfall_id] = oracle_id
                else:
                    logger.warning("No oracle_id in Scryfall response", scryfall_id=scryfall_id)
                return oracle_id
            except Exception as e:
                logger.error(
                    "Failed to fetch oracle_id from Scryfall",
                    scryfall_id=scryfall_id,
                    attempt=attempt,
                    error=str(e),
                )
                if attempt < MAX_RETRIES:
                    delay = min(1000 * (2 ** (attempt - 1)), 5000)
                    await asyncio.sleep(delay / 1000)

        return None

    # Note: close() is no longer needed as we use a shared client

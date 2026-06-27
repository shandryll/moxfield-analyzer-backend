import asyncio
import json
import os
from loguru import logger
from src.infrastructure.playwright.browser_pool import BrowserPool, get_browser_pool
from src.infrastructure.utils.cache import deck_cache
from src.shared.exceptions import MoxfieldError, NotFoundMoxfieldError

MOXFIELD_API_BASE = os.getenv("MOXFIELD_API_BASE_URL", "https://api2.moxfield.com")
MOXFIELD_TIMEOUT_MS = int(os.getenv("MOXFIELD_TIMEOUT_MS", "30000"))


class MoxfieldDeckRepository:
    def __init__(self, browser_pool: BrowserPool | None = None) -> None:
        self._browser_pool = browser_pool or get_browser_pool()
        self._fetch_locks: dict[str, asyncio.Lock] = {}

    async def get_by_id(self, deck_id: str) -> dict:
        cached = deck_cache.get(deck_id)
        if cached:
            logger.info("Returning cached deck", deck_id=deck_id)
            return cached

        if deck_id not in self._fetch_locks:
            self._fetch_locks[deck_id] = asyncio.Lock()

        async with self._fetch_locks[deck_id]:
            cached = deck_cache.get(deck_id)
            if cached:
                logger.info("Returning cached deck (after lock)", deck_id=deck_id)
                return cached

            logger.info("Fetching deck from Moxfield", deck_id=deck_id)
            raw = await self._fetch_with_playwright(deck_id)
            deck_data = self._payload_to_raw(raw)
            deck_cache[deck_id] = deck_data
            logger.info(
                "Deck fetched successfully",
                deck_id=deck_id,
                deck_name=deck_data.get("name"),
            )

        self._fetch_locks.pop(deck_id, None)
        return deck_data

    async def _fetch_with_playwright(self, deck_id: str, retries: int = 1) -> dict:
        url = f"{MOXFIELD_API_BASE}/v3/decks/all/{deck_id}"

        for attempt in range(1, retries + 2):
            try:
                page = await self._browser_pool.get_page()
                try:
                    response = await page.goto(url, wait_until="networkidle", timeout=MOXFIELD_TIMEOUT_MS)
                    if not response:
                        raise Exception("Nenhuma resposta recebida do Moxfield")

                    status = response.status

                    if status == 404:
                        raise NotFoundMoxfieldError(deck_id)
                    if status < 200 or status >= 300:
                        raise MoxfieldError(status, f"HTTP {status}")

                    content_type = response.headers.get("content-type", "")
                    if "text/html" in content_type:
                        body = await page.content()
                        if "<!DOCTYPE html>" in body or "<html" in body:
                            raise Exception("Cloudflare bloqueou a requisição")

                    text = await response.text()
                    if not text or not text.strip():
                        raise Exception("Resposta vazia do Moxfield")

                    payload = json.loads(text)
                    logger.info("Deck fetched via Playwright", deck_id=deck_id, status=status)
                    return payload
                finally:
                    await page.context.close()
            except (NotFoundMoxfieldError, MoxfieldError):
                raise
            except Exception as e:
                logger.error("Playwright fetch failed", deck_id=deck_id, attempt=attempt, error=str(e))
                if attempt > retries:
                    raise
                delay = min(1000 * (2 ** (attempt - 1)), 5000)
                await asyncio.sleep(delay / 1000)

        raise Exception(f"Falha ao buscar deck após {retries + 1} tentativas")

    @staticmethod
    def _payload_to_raw(payload: dict) -> dict:
        boards = payload.get("boards", {}) or {}

        def get_cards(board_name: str) -> dict:
            board = boards.get(board_name, {}) or {}
            return board.get("cards", {}) or {}

        return {
            "id": payload.get("id", ""),
            "name": payload.get("name", ""),
            "description": payload.get("description", ""),
            "public_url": payload.get("publicUrl", ""),
            "mainboard": get_cards("mainboard"),
            "commanders": get_cards("commanders"),
            "companions": get_cards("companions"),
            "sideboard": get_cards("sideboard"),
            "created_at": str(payload.get("createdAtUtc", "")),
            "updated_at": str(payload.get("lastUpdatedAtUtc", "")),
        }

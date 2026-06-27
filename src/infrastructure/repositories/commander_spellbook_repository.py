import hashlib
import json
import os
import httpx
from loguru import logger
from src.shared.models import Card, ComboCardInfo
from src.shared.exceptions import (
    CommanderSpellbookApiError,
    CommanderSpellbookError,
    CommanderSpellbookRateLimitError,
    CommanderSpellbookTimeoutError,
)
from src.infrastructure.utils.http_client import get_http_client
from src.infrastructure.utils.cache import combo_cache

API_BASE_URL = os.getenv(
    "COMMANDER_SPELLBOOK_API_BASE_URL",
    "https://backend.commanderspellbook.com"
)
WEB_BASE_URL = os.getenv(
    "COMMANDER_SPELLBOOK_WEB_BASE_URL",
    "https://commanderspellbook.com"
)
TIMEOUT = float(os.getenv("COMMANDER_SPELLBOOK_TIMEOUT_SECONDS", "30"))


class CommanderSpellbookRepository:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or get_http_client(timeout=TIMEOUT)

    async def find_for_cards(
        self,
        mainboard: list[Card],
        commanders: list[Card],
    ) -> list[ComboCardInfo]:
        cache_key = self._build_cache_key(mainboard, commanders)
        cached = combo_cache.get(cache_key)
        if cached is not None:
            logger.info("Returning cached combos", cache_key=cache_key)
            return cached

        logger.info(
            "Finding combos by card list",
            mainboard_count=len(mainboard),
            commanders_count=len(commanders),
        )

        payload = {
            "main": [{"card": c.name, "quantity": c.quantity} for c in mainboard],
            "commanders": [{"card": c.name, "quantity": c.quantity} for c in commanders],
        }

        ordering = "-popularity,identity_count,card_count,-created"
        q = "legal:commander"
        url = f"{API_BASE_URL}/find-my-combos?ordering={ordering}&q={q}"

        try:
            response = await self._client.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Moxfield-Analyzer/2.0",
                },
            )

            if response.status_code == 404:
                logger.warning("Commander Spellbook API returned 404")
                return []

            if response.status_code >= 400:
                logger.error(
                    "Commander Spellbook API error",
                    status=response.status_code,
                )
                raise CommanderSpellbookApiError(
                    status=response.status_code,
                    message=f"API returned status {response.status_code}",
                )

            data = response.json()
            included: list[dict] = []
            if (
                isinstance(data, dict)
                and isinstance(data.get("results"), dict)
                and isinstance(data["results"].get("included"), list)
            ):
                included = data["results"]["included"]

            logger.info("Combos found successfully", included_count=len(included))

            results: list[ComboCardInfo] = []
            for combo in included:
                card_names = [
                    str(u.get("card", {}).get("name", ""))
                    for u in combo.get("uses", [])
                    if isinstance(u, dict)
                ]
                combo_results = [
                    str(p.get("feature", {}).get("name", ""))
                    for p in combo.get("produces", [])
                    if isinstance(p, dict)
                ]
                results.append(
                    ComboCardInfo(
                        id=combo.get("id", ""),
                        card_names=card_names,
                        results=combo_results,
                        description=combo.get("description"),
                        identity=combo.get("identity"),
                        mana_needed=combo.get("manaNeeded"),
                        prerequisites=combo.get("notablePrerequisites"),
                        commander_spellbook_url=f"{WEB_BASE_URL}/combo/{combo.get('id', '')}",
                    )
                )

            combo_cache[cache_key] = results
            return results
        except httpx.TimeoutException:
            raise CommanderSpellbookTimeoutError("Commander Spellbook API timed out")
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                raise CommanderSpellbookRateLimitError("Rate limit exceeded on Commander Spellbook API")
            raise CommanderSpellbookError(f"Error fetching combos: {err_str}")

    @staticmethod
    def _build_cache_key(mainboard: list[Card], commanders: list[Card]) -> str:
        entries = sorted((c.name, c.quantity, False) for c in mainboard)
        entries += sorted((c.name, c.quantity, True) for c in commanders)
        raw = json.dumps(entries, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

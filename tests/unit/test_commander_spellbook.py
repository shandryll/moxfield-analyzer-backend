import httpx
import pytest
from src.shared.models import Card


class TestCommanderSpellbookRepository:
    def _make_card(self, name: str, quantity: int = 1) -> Card:
        return Card(
            name=name,
            type_line="",
            mana_cost="",
            cmc=0,
            quantity=quantity,
        )

    @pytest.mark.asyncio
    async def test_find_combos_returns_list(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url="https://backend.commanderspellbook.com/find-my-combos?ordering=-popularity,identity_count,card_count,-created&q=legal:commander",
            json={
                "results": {
                    "included": [
                        {
                            "id": "123",
                            "description": "Gravecrawler combo",
                            "uses": [
                                {"card": {"name": "Gravecrawler"}},
                                {"card": {"name": "Phyrexian Altar"}},
                            ],
                            "produces": [
                                {"feature": {"name": "Infinite death trigger"}},
                            ],
                            "manaNeeded": "{B}",
                        }
                    ]
                }
            },
        )

        from src.infrastructure.repositories.commander_spellbook_repository import (
            CommanderSpellbookRepository,
        )
        repo = CommanderSpellbookRepository()
        cards = [self._make_card("Gravecrawler")]
        result = await repo.find_for_cards(cards, [])
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].description == "Gravecrawler combo"
        assert "Gravecrawler" in result[0].card_names

    @pytest.mark.asyncio
    async def test_find_combos_returns_empty_on_404(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url="https://backend.commanderspellbook.com/find-my-combos?ordering=-popularity,identity_count,card_count,-created&q=legal:commander",
            status_code=404,
        )

        from src.infrastructure.repositories.commander_spellbook_repository import (
            CommanderSpellbookRepository,
        )
        repo = CommanderSpellbookRepository()
        cards = [self._make_card("Unknown")]
        result = await repo.find_for_cards(cards, [])
        assert result == []

    @pytest.mark.asyncio
    async def test_find_combos_returns_empty_on_timeout(self, httpx_mock):
        httpx_mock.add_exception(
            httpx.TimeoutException("Connection timed out"),
            method="POST",
            url="https://backend.commanderspellbook.com/find-my-combos?ordering=-popularity,identity_count,card_count,-created&q=legal:commander",
        )

        from src.infrastructure.repositories.commander_spellbook_repository import (
            CommanderSpellbookRepository,
        )
        from src.shared.exceptions import CommanderSpellbookTimeoutError

        repo = CommanderSpellbookRepository()
        cards = [self._make_card("Unknown")]
        with pytest.raises(CommanderSpellbookTimeoutError):
            await repo.find_for_cards(cards, [])

from unittest.mock import patch
import pytest
from httpx import AsyncClient, ASGITransport
from src.infrastructure.http.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestAPI:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OK"
        assert data["version"] == "1.0.0"
        assert "environment" in data
        assert "timestamp" in data
        assert "documentation" in data

    async def test_root_returns_not_found(self, client):
        resp = await client.get("/")
        assert resp.status_code == 404

    async def test_validate_missing_url(self, client):
        resp = await client.get("/api/deck/validate")
        assert resp.status_code == 422

    async def test_validate_missing_kindred(self, client):
        resp = await client.get(
            "/api/deck/validate",
            params={"url": "https://moxfield.com/decks/some-id"},
        )
        assert resp.status_code == 422

    async def test_validate_with_params(self, client):
        resp = await client.get(
            "/api/deck/validate",
            params={
                "url": "https://moxfield.com/decks/nonexistent-id",
                "kindred": "Elf",
            },
        )
        assert resp.status_code == 404

    async def test_not_found_route(self, client):
        resp = await client.get("/nonexistent")
        assert resp.status_code == 404

    async def test_cors_headers(self, client):
        resp = await client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    async def test_rate_limit_exceeded_on_validate(self, app, client):
        from src.shared.exceptions import NotFoundMoxfieldError

        with patch(
            "src.application.use_cases.validate_deck.MoxfieldDeckRepository.get_by_id",
        ) as mock_get:
            mock_get.side_effect = NotFoundMoxfieldError("not found")
            for _ in range(10):
                resp = await client.get(
                    "/api/deck/validate",
                    params={"url": "https://moxfield.com/decks/test", "kindred": "Elf"},
                )
                assert resp.status_code == 404

            resp = await client.get(
                "/api/deck/validate",
                params={"url": "https://moxfield.com/decks/test", "kindred": "Elf"},
            )
            assert resp.status_code == 429

    async def test_validate_full_flow_with_mocked_moxfield(self, app, client):
        mock_raw = {
            "id": "test-id-123",
            "name": "Test Deck",
            "description": "A test deck",
            "public_url": "https://moxfield.com/decks/test",
            "mainboard": {
                "c1": {
                    "card": {
                        "name": "Elvish Mystic",
                        "scryfall_id": "sf-1",
                        "type_line": "Creature — Elf Druid",
                        "mana_cost": "{G}",
                        "cmc": 1,
                        "colors": ["G"],
                        "color_identity": ["G"],
                        "oracle_text": "{T}: Add {G}.",
                        "power": "1",
                        "toughness": "1",
                        "keywords": [],
                        "image_uris": {"normal": "https://cards.scryfall.io/normal/front.png"},
                    },
                    "quantity": 3,
                },
            },
            "commanders": {
                "c2": {
                    "card": {
                        "name": "Ezuri, Renegade Leader",
                        "scryfall_id": "sf-2",
                        "type_line": "Legendary Creature — Elf Warrior",
                        "mana_cost": "{1}{G}{G}",
                        "cmc": 3,
                        "colors": ["G"],
                        "color_identity": ["G"],
                        "oracle_text": "{T}: Regenerate target Elf.",
                        "power": "2",
                        "toughness": "2",
                        "keywords": [],
                        "image_uris": {"normal": "https://cards.scryfall.io/normal/front.png"},
                    },
                    "quantity": 1,
                },
            },
            "companions": {},
            "sideboard": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        with (
            patch(
                "src.application.use_cases.validate_deck.MoxfieldDeckRepository.get_by_id",
                return_value=mock_raw,
            ),
            patch(
                "src.application.use_cases.validate_deck.ScryfallCardResolver.resolve",
                return_value={"sf-1": None, "sf-2": None},
            ),
            patch(
                "src.application.use_cases.validate_deck.CommanderSpellbookRepository.find_for_cards",
                return_value=[],
            ),
        ):
            resp = await client.get(
                "/api/deck/validate",
                params={"url": "https://moxfield.com/decks/test-id-123", "kindred": "Elf"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Test Deck"
            assert data["kindred_wars"]["kindred"] == "Elf"
            assert len(data["commanders"]) == 1
            assert data["commanders"][0]["name"] == "Ezuri, Renegade Leader"

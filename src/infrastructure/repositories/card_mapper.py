import os
from src.shared.models import Card, CardFace
from src.shared.models.oracle_tag import OracleTag
from src.infrastructure.static_data.oracle_tags import get_tags_for_oracle_id

SCRYFALL_IMAGE_BASE = os.getenv(
    "SCRYFALL_IMAGE_BASE_URL",
    "https://cards.scryfall.io/normal"
)


class CardMapper:
    @staticmethod
    def _scryfall_image_url(scryfall_id: str, side: str = "front") -> str:
        first = scryfall_id[0]
        second = scryfall_id[1]
        return f"{SCRYFALL_IMAGE_BASE}/{side}/{first}/{second}/{scryfall_id}.jpg"

    @staticmethod
    def _map_card_faces(raw: list | None, sf_id: str) -> list[CardFace] | None:
        if not raw:
            return None
        faces: list[CardFace] = []
        for i, face in enumerate(raw):
            if not isinstance(face, dict):
                continue
            side = "front" if i == 0 else "back"
            faces.append(
                CardFace(
                    name=face.get("name"),
                    mana_cost=face.get("mana_cost"),
                    type_line=face.get("type_line"),
                    oracle_text=face.get("oracle_text"),
                    power=face.get("power"),
                    toughness=face.get("toughness"),
                    loyalty=face.get("loyalty"),
                    colors=[str(c) for c in face.get("colors", []) if isinstance(c, str)],
                    image_url=CardMapper._scryfall_image_url(sf_id, side),
                )
            )
        return faces if faces else None

    def extract_scryfall_ids(self, board: dict) -> list[str]:
        ids: list[str] = []
        for slot in board.values():
            if not isinstance(slot, dict):
                continue
            card = slot.get("card", {})
            if not isinstance(card, dict):
                continue
            sf_id = card.get("scryfall_id")
            if isinstance(sf_id, str):
                ids.append(sf_id)
        return ids

    def board_to_cards(
        self,
        board: dict,
        oracle_id_map: dict[str, str],
    ) -> list[Card]:
        cards: list[Card] = []
        for slot in board.values():
            if not isinstance(slot, dict):
                continue
            card = slot.get("card", {})
            if not isinstance(card, dict):
                continue
            quantity = slot.get("quantity", 1)
            if not isinstance(quantity, (int, float)):
                quantity = 1
            sf_id = card.get("scryfall_id")
            sf_id = str(sf_id) if isinstance(sf_id, str) else None
            oracle_id = oracle_id_map.get(sf_id, None) if sf_id else None
            oracle_id = str(oracle_id) if oracle_id else None

            card_faces = self._map_card_faces(
                card.get("card_faces"), sf_id
            ) if sf_id else None

            tags: list[OracleTag] = []
            if oracle_id:
                tags = get_tags_for_oracle_id(oracle_id)

            cards.append(
                Card(
                    name=str(card.get("name", "Unknown")),
                    type_line=str(card.get("type_line", "")),
                    mana_cost=str(card.get("mana_cost", "")),
                    cmc=float(card.get("cmc", 0) or 0),
                    quantity=int(quantity),
                    oracle_text=str(card.get("oracle_text")) if card.get("oracle_text") else None,
                    power=str(card.get("power")) if card.get("power") else None,
                    toughness=str(card.get("toughness")) if card.get("toughness") else None,
                    loyalty=str(card.get("loyalty")) if card.get("loyalty") else None,
                    keywords=[str(k) for k in card.get("keywords", []) if isinstance(k, str)],
                    colors=[str(c) for c in card.get("colors", []) if isinstance(c, str)],
                    color_identity=[str(c) for c in card.get("color_identity", []) if isinstance(c, str)],
                    image_url=self._scryfall_image_url(sf_id) if sf_id else None,
                    oracle_id=oracle_id,
                    tags=tags,
                    card_faces=card_faces,
                )
            )
        return cards

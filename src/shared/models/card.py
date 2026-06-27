from pydantic import BaseModel
from .card_face import CardFace
from .oracle_tag import OracleTag


class Card(BaseModel):
    name: str
    type_line: str
    mana_cost: str
    cmc: float
    quantity: int
    oracle_text: str | None = None
    power: str | None = None
    toughness: str | None = None
    loyalty: str | None = None
    keywords: list[str] = []
    colors: list[str] = []
    color_identity: list[str] = []
    image_url: str | None = None
    oracle_id: str | None = None
    tags: list[OracleTag] = []
    card_faces: list[CardFace] | None = None

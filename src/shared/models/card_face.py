from pydantic import BaseModel


class CardFace(BaseModel):
    name: str | None = None
    mana_cost: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    power: str | None = None
    toughness: str | None = None
    loyalty: str | None = None
    colors: list[str] = []
    image_url: str | None = None

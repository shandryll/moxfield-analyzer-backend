from pydantic import BaseModel


class ComboCardInfo(BaseModel):
    id: str
    card_names: list[str] = []
    results: list[str] = []
    description: str | None = None
    identity: str | None = None
    mana_needed: str | None = None
    prerequisites: str | None = None
    commander_spellbook_url: str | None = None

from pydantic import BaseModel
from .card import Card
from .kindred_wars import KindredWars
from .mana_curve import ManaCurveEntry
from .commander_spellbook import ComboCardInfo


class DeckDetails(BaseModel):
    id: str
    name: str
    description: str = ""
    public_url: str = ""
    total_cards: int = 0
    creatures: int = 0
    non_creatures: int = 0
    commander_creatures: int = 0
    companion_creatures: int = 0
    creatures_including_commanders: int = 0
    mana_curve: list[ManaCurveEntry] = []
    kindred_wars: KindredWars | None = None
    find_my_combos: list[ComboCardInfo] = []
    cards: list[Card] = []
    commanders: list[Card] = []
    companions: list[Card] = []
    created_at: str = ""
    updated_at: str = ""

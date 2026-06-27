from pydantic import BaseModel
from .tag_stats import TagStats


class KindredWars(BaseModel):
    kindred: str
    score: int = 0
    creatures_with_kindred_identity: int | None = None
    all_validated_creatures: bool | None = None
    non_validated_creatures: list[str] | None = None
    companion_rule_applied: bool | None = None
    expected_total_creatures: int | None = None
    reserved_list: TagStats = TagStats()
    game_changer: TagStats = TagStats()
    banned_cards: TagStats = TagStats()
    potential_tutor: TagStats = TagStats()
    potential_mass_removal: TagStats = TagStats()
    potential_extra_turn: TagStats = TagStats()

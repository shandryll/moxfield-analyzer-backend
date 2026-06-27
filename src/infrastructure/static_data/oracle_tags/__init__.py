from src.shared.models.oracle_tag import OracleTag
from .banned_cards import BANNED_CARDS_IDS
from .extra_turn import EXTRA_TURN_IDS
from .game_changer import GAME_CHANGER_IDS
from .mass_removal import MASS_REMOVAL_IDS
from .reserved_list import RESERVED_LIST_IDS
from .tutor import TUTOR_IDS

ORACLE_TAG_LISTS: dict[OracleTag, set[str]] = {
    OracleTag.MASS_REMOVAL: MASS_REMOVAL_IDS,
    OracleTag.TUTOR: TUTOR_IDS,
    OracleTag.EXTRA_TURN: EXTRA_TURN_IDS,
    OracleTag.BANNED_CARDS: BANNED_CARDS_IDS,
    OracleTag.RESERVED_LIST: RESERVED_LIST_IDS,
    OracleTag.GAME_CHANGER: GAME_CHANGER_IDS,
}

_ORACLE_ID_TO_TAGS: dict[str, list[OracleTag]] = {}
for _tag, _ids in ORACLE_TAG_LISTS.items():
    for _oid in _ids:
        _ORACLE_ID_TO_TAGS.setdefault(_oid, []).append(_tag)


def get_tags_for_oracle_id(oracle_id: str) -> list[OracleTag]:
    return _ORACLE_ID_TO_TAGS.get(oracle_id, [])

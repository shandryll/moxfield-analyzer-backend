import re
from src.shared.models import Card, KindredWars, TagStats
from .tags.tag_service import TagService
from .tags.calculators.base import TagCalculator
from .card_type_helper import CardTypeHelper

KINDRED_WARS_POINTS_BY_CMC: dict[int, int] = {
    1: 5,
    2: 4,
    3: 3,
    4: 2,
    5: 1,
}


class KindredWarsCalculator:
    def __init__(self, tag_service: TagService | None = None) -> None:
        self._tag_service = tag_service or self._create_default_tag_service()

    @staticmethod
    def _create_default_tag_service() -> TagService:
        svc = TagService()
        svc.register_calculator(TagCalculator("tutor"))
        svc.register_calculator(TagCalculator("mass-removal"))
        svc.register_calculator(TagCalculator("extra-turn"))
        svc.register_calculator(TagCalculator("banned-cards"))
        svc.register_calculator(TagCalculator("game-changer"))
        svc.register_calculator(TagCalculator("reserved-list"))
        return svc

    def calculate_kindred_wars(
        self,
        all_cards: list[Card],
        mainboard: dict,
        commanders: dict,
        companions: dict,
        kindred: str | None,
        creatures_including_commanders: int,
    ) -> KindredWars:
        kindred_label = kindred or "not informed"
        sanitized_kindred = re.escape(kindred) if kindred else None

        score = self._calculate_score(mainboard, companions)

        identity_count = 0
        non_validated: list[str] | None = None

        if sanitized_kindred:
            non_validated = []
            identity_count += self._count_identity_in_board(
                mainboard, sanitized_kindred, non_validated, False
            )
            identity_count += self._count_identity_in_board(
                commanders, sanitized_kindred, non_validated, True
            )
            identity_count += self._count_identity_in_board(
                companions, sanitized_kindred, non_validated, False
            )

        has_companions = len(companions) > 0
        all_validated = None
        expected_total = None

        if sanitized_kindred:
            all_validated = identity_count == creatures_including_commanders
            if has_companions:
                mc = CardTypeHelper.count_creatures(mainboard, False)
                cc = CardTypeHelper.count_creatures(commanders, True)
                compc = CardTypeHelper.count_creatures(companions, False)
                expected_total = mc + cc + compc

        all_tag_stats = self._tag_service.calculate_all(all_cards)

        return KindredWars(
            kindred=kindred_label,
            score=score,
            creatures_with_kindred_identity=identity_count if sanitized_kindred else None,
            all_validated_creatures=all_validated,
            non_validated_creatures=non_validated if sanitized_kindred else None,
            companion_rule_applied=has_companions if sanitized_kindred else None,
            expected_total_creatures=expected_total,
            reserved_list=all_tag_stats.get("reserved-list", TagStats()),
            game_changer=all_tag_stats.get("game-changer", TagStats()),
            banned_cards=all_tag_stats.get("banned-cards", TagStats()),
            potential_tutor=all_tag_stats.get("tutor", TagStats()),
            potential_mass_removal=all_tag_stats.get("mass-removal", TagStats()),
            potential_extra_turn=all_tag_stats.get("extra-turn", TagStats()),
        )

    def _calculate_score(self, mainboard: dict, companions: dict) -> int:
        score = 0
        for board in (mainboard, companions):
            for slot in board.values():
                card = slot.get("card", {}) if isinstance(slot, dict) else {}
                quantity = slot.get("quantity", 1) if isinstance(slot, dict) else 1
                type_line = CardTypeHelper.get_front_face_type_line(card)
                if CardTypeHelper.is_creature_or_commander_planeswalker(type_line, False):
                    cmc = int(card.get("cmc", 0)) if isinstance(card, dict) else 0
                    score += KINDRED_WARS_POINTS_BY_CMC.get(cmc, 0) * quantity
        return score

    def _count_identity_in_board(
        self,
        board: dict,
        kindred: str,
        non_validated: list[str],
        is_commander: bool,
    ) -> int:
        count = 0
        for slot in board.values():
            card = slot.get("card", {}) if isinstance(slot, dict) else {}
            quantity = slot.get("quantity", 1) if isinstance(slot, dict) else 1
            card_name = str(card.get("name", "Unknown Card"))
            type_line = CardTypeHelper.get_front_face_type_line(card)

            if self._matches_kindred(card, kindred):
                count += quantity
            elif CardTypeHelper.is_creature_or_commander_planeswalker(type_line, is_commander):
                if card_name not in non_validated:
                    non_validated.append(card_name)
        return count

    @staticmethod
    def _matches_kindred(card: dict, kindred: str) -> bool:
        term = kindred.lower()
        faces = card.get("card_faces")
        if isinstance(faces, list) and faces:
            for face in faces:
                if isinstance(face, dict):
                    tl = str(face.get("type_line", "")).lower()
                    ot = str(face.get("oracle_text", "")).lower()
                    if term in tl or term in ot:
                        return True
        tl = str(card.get("type_line", "")).lower()
        ot = str(card.get("oracle_text", "")).lower()
        return term in tl or term in ot

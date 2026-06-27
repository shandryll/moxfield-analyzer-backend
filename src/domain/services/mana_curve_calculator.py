from src.shared.models import ManaCurveEntry
from .card_type_helper import CardTypeHelper

LANDS_KEYWORDS = {"land", "terreno", "terra"}


class ManaCurveCalculator:
    def build_mana_curve(
        self,
        mainboard: dict,
        commanders: dict | None = None,
    ) -> list[ManaCurveEntry]:
        cmc_counts: dict[int, int] = {}

        for slot in mainboard.values():
            card = slot.get("card", {}) if isinstance(slot, dict) else {}
            quantity = slot.get("quantity", 1) if isinstance(slot, dict) else 1
            type_line = CardTypeHelper.get_front_face_type_line(card)
            if self._is_land(type_line):
                continue
            cmc = int(card.get("cmc", 0)) if isinstance(card, dict) else 0
            cmc_counts[cmc] = cmc_counts.get(cmc, 0) + quantity

        commanders = commanders or {}
        for slot in commanders.values():
            card = slot.get("card", {}) if isinstance(slot, dict) else {}
            quantity = slot.get("quantity", 1) if isinstance(slot, dict) else 1
            type_line = CardTypeHelper.get_front_face_type_line(card)
            if self._is_land(type_line):
                continue
            cmc = int(card.get("cmc", 0)) if isinstance(card, dict) else 0
            cmc_counts[cmc] = cmc_counts.get(cmc, 0) + quantity

        return sorted(
            [ManaCurveEntry(cmc=cmc, count=count) for cmc, count in cmc_counts.items()],
            key=lambda e: e.cmc,
        )

    @staticmethod
    def _is_land(type_line: str) -> bool:
        return any(kw in type_line.lower() for kw in LANDS_KEYWORDS)

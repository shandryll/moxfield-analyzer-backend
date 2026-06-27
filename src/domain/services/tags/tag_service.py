from src.shared.models import Card, TagStats
from .calculators.base import TagCalculator


class TagService:
    def __init__(self) -> None:
        self._calculators: dict[str, TagCalculator] = {}

    def register_calculator(self, calculator: TagCalculator) -> None:
        self._calculators[calculator.tag_name] = calculator

    def calculate_all(self, cards: list[Card]) -> dict[str, TagStats]:
        results: dict[str, TagStats] = {}
        for tag_name, calc in self._calculators.items():
            try:
                results[tag_name] = calc.calculate(cards)
            except Exception:
                results[tag_name] = TagStats()
        return results

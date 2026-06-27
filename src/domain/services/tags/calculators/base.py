from src.shared.models import Card, TagStats


class TagCalculator:
    def __init__(self, tag_name: str) -> None:
        self.tag_name = tag_name

    def calculate(self, cards: list[Card]) -> TagStats:
        filtered = [c for c in cards if self.tag_name in c.tags]
        return TagStats(
            total=len(filtered),
            cards=[c.name for c in filtered],
        )

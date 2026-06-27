from src.domain.services.kindred_wars_calculator import KindredWarsCalculator
from src.shared.models import Card


class TestKindredWarsCalculator:
    def setup_method(self):
        self.calc = KindredWarsCalculator()

    def _make_card(self, name: str, tags: list[str] | None = None) -> Card:
        return Card(
            name=name,
            type_line="",
            mana_cost="",
            cmc=0,
            quantity=1,
            oracle_text=None,
            power=None,
            toughness=None,
            loyalty=None,
            keywords=[],
            colors=[],
            color_identity=[],
            image_url=None,
            oracle_id=None,
            tags=tags or [],
        )

    def test_score_based_on_cmc(self):
        mainboard = {
            "c1": {"card": {"type_line": "Creature", "cmc": 1}, "quantity": 2},
            "c2": {"card": {"type_line": "Creature", "cmc": 2}, "quantity": 3},
        }
        result = self.calc.calculate_kindred_wars([], mainboard, {}, {}, None, 5)
        assert result.score == 22

    def test_non_creatures_not_counted(self):
        mainboard = {
            "c": {"card": {"type_line": "Creature", "cmc": 1}, "quantity": 1},
            "i": {"card": {"type_line": "Instant", "cmc": 1}, "quantity": 1},
        }
        result = self.calc.calculate_kindred_wars([], mainboard, {}, {}, None, 1)
        assert result.score == 5

    def test_tag_statistics(self):
        cards = [
            self._make_card("Demonic Tutor", ["tutor"]),
            self._make_card("Cyclonic Rift", ["mass-removal"]),
            self._make_card("Time Warp", ["extra-turn"]),
        ]
        result = self.calc.calculate_kindred_wars(cards, {}, {}, {}, None, 0)
        assert result.potential_tutor.total == 1
        assert result.potential_tutor.cards == ["Demonic Tutor"]
        assert result.potential_mass_removal.total == 1
        assert result.potential_extra_turn.total == 1

    def test_banned_cards(self):
        cards = [
            self._make_card("Sol Ring", ["banned-cards"]),
            self._make_card("Lotus Petal", ["banned-cards"]),
        ]
        result = self.calc.calculate_kindred_wars(cards, {}, {}, {}, None, 0)
        assert result.banned_cards.total == 2
        assert "Sol Ring" in result.banned_cards.cards

    def test_kindred_not_informed(self):
        result = self.calc.calculate_kindred_wars([], {}, {}, {}, None, 0)
        assert result.kindred == "not informed"

    def test_zero_score_no_creatures(self):
        mainboard = {
            "i": {"card": {"type_line": "Instant", "cmc": 1}, "quantity": 10},
        }
        result = self.calc.calculate_kindred_wars([], mainboard, {}, {}, None, 0)
        assert result.score == 0

    def test_zero_points_for_cmc_above_5(self):
        mainboard = {
            "c": {"card": {"type_line": "Creature", "cmc": 7}, "quantity": 1},
        }
        result = self.calc.calculate_kindred_wars([], mainboard, {}, {}, None, 1)
        assert result.score == 0

    def test_kindred_identity_validation(self):
        mainboard = {
            "e1": {
                "card": {
                    "name": "Llanowar Elves",
                    "type_line": "Creature — Elf",
                    "oracle_text": "",
                },
                "quantity": 3,
            },
            "h": {
                "card": {
                    "name": "Human Soldier",
                    "type_line": "Creature — Human",
                    "oracle_text": "",
                },
                "quantity": 1,
            },
        }
        result = self.calc.calculate_kindred_wars([], mainboard, {}, {}, "Elf", 4)
        assert result.creatures_with_kindred_identity == 3
        assert result.non_validated_creatures == ["Human Soldier"]

    def test_kindred_matches_double_faced_card(self):
        mainboard = {
            "dfc": {
                "card": {
                    "name": "Westvale Abbey",
                    "type_line": "Land",
                    "oracle_text": "",
                    "card_faces": [
                        {
                            "name": "Westvale Abbey",
                            "type_line": "Land",
                            "oracle_text": "",
                        },
                        {
                            "name": "Ormendahl, Profane Prince",
                            "type_line": "Legendary Creature — Demon",
                            "oracle_text": "",
                        },
                    ],
                },
                "quantity": 1,
            },
            "demon": {
                "card": {
                    "name": "Shadowborn Demon",
                    "type_line": "Creature — Demon",
                    "oracle_text": "",
                },
                "quantity": 1,
            },
        }
        result = self.calc.calculate_kindred_wars([], mainboard, {}, {}, "Demon", 2)
        assert result.creatures_with_kindred_identity == 2
        assert result.non_validated_creatures == []

from src.domain.services.mana_curve_calculator import ManaCurveCalculator


class TestManaCurveCalculator:
    def setup_method(self):
        self.calc = ManaCurveCalculator()

    def test_build_curve_correctly(self):
        mainboard = {
            "card1": {"card": {"type_line": "Creature", "cmc": 1}, "quantity": 2},
            "card2": {"card": {"type_line": "Creature", "cmc": 2}, "quantity": 3},
        }
        result = self.calc.build_mana_curve(mainboard)
        assert len(result) == 2
        assert result[0].cmc == 1 and result[0].count == 2
        assert result[1].cmc == 2 and result[1].count == 3

    def test_exclude_lands(self):
        mainboard = {
            "c1": {"card": {"type_line": "Creature", "cmc": 1}, "quantity": 1},
            "c2": {"card": {"type_line": "Land — Forest", "cmc": 0}, "quantity": 10},
        }
        result = self.calc.build_mana_curve(mainboard)
        assert len(result) == 1
        assert result[0].cmc == 1

    def test_include_commanders(self):
        mainboard = {
            "c1": {"card": {"type_line": "Creature", "cmc": 1}, "quantity": 1},
        }
        commanders = {
            "cmd": {"card": {"type_line": "Legendary Creature", "cmc": 3}, "quantity": 1},
        }
        result = self.calc.build_mana_curve(mainboard, commanders)
        assert len(result) == 2

    def test_empty_mainboard(self):
        result = self.calc.build_mana_curve({})
        assert result == []

    def test_only_lands(self):
        mainboard = {
            "c1": {"card": {"type_line": "Land", "cmc": 0}, "quantity": 20},
        }
        result = self.calc.build_mana_curve(mainboard)
        assert result == []

    def test_exclude_portuguese_lands(self):
        mainboard = {
            "c1": {"card": {"type_line": "Terreno — Floresta", "cmc": 0}, "quantity": 10},
            "c2": {"card": {"type_line": "Terra", "cmc": 0}, "quantity": 5},
            "c3": {"card": {"type_line": "Creature", "cmc": 2}, "quantity": 1},
        }
        result = self.calc.build_mana_curve(mainboard)
        assert len(result) == 1
        assert result[0].cmc == 2

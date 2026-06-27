from src.infrastructure.repositories.card_mapper import CardMapper


class TestCardMapper:
    def setup_method(self):
        self.mapper = CardMapper()

    def test_extract_scryfall_ids(self):
        board = {
            "c1": {"card": {"scryfall_id": "abc-123"}},
            "c2": {"card": {"scryfall_id": "def-456"}},
        }
        ids = self.mapper.extract_scryfall_ids(board)
        assert ids == ["abc-123", "def-456"]

    def test_ignore_cards_without_scryfall_id(self):
        board = {
            "c1": {"card": {"scryfall_id": "abc-123"}},
            "c2": {"card": {"name": "No ID"}},
        }
        ids = self.mapper.extract_scryfall_ids(board)
        assert ids == ["abc-123"]

    def test_empty_board(self):
        assert self.mapper.extract_scryfall_ids({}) == []

    def test_board_to_cards(self):
        board = {
            "c1": {
                "card": {"name": "Card 1", "scryfall_id": "id-1", "cmc": 1},
                "quantity": 2,
            },
            "c2": {
                "card": {"name": "Card 2", "scryfall_id": "id-2", "cmc": 2},
                "quantity": 3,
            },
        }
        oracle_map = {"id-1": "oracle-1", "id-2": "oracle-2"}
        cards = self.mapper.board_to_cards(board, oracle_map)
        assert len(cards) == 2
        assert cards[0].name == "Card 1"
        assert cards[0].quantity == 2
        assert cards[1].name == "Card 2"
        assert cards[1].quantity == 3

    def test_tags_assigned_from_oracle_id(self):
        board = {
            "c1": {
                "card": {"name": "Wrath of God", "scryfall_id": "id-wrath"},
                "quantity": 1,
            },
        }
        known_mass_removal_id = "1a1a16e5-ce4f-42b8-a1c6-05dd635d83cc"
        oracle_map = {"id-wrath": known_mass_removal_id}
        cards = self.mapper.board_to_cards(board, oracle_map)
        assert "mass-removal" in cards[0].tags
        assert "tutor" not in cards[0].tags

    def test_default_quantity(self):
        board = {
            "c1": {
                "card": {"name": "Card 1", "scryfall_id": "id-1"},
            },
        }
        cards = self.mapper.board_to_cards(board, {})
        assert cards[0].quantity == 1

    def test_empty_board_returns_empty(self):
        assert self.mapper.board_to_cards({}, {}) == []

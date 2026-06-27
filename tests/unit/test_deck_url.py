import pytest
from src.domain.value_objects.deck_url import DeckUrl


class TestDeckUrl:
    def test_extract_id_from_full_url(self):
        url = "https://moxfield.com/decks/abc-123"
        assert DeckUrl(url).value == "abc-123"

    def test_extract_id_from_url_without_www(self):
        url = "https://moxfield.com/decks/abc123"
        assert DeckUrl(url).value == "abc123"

    def test_extract_id_from_url_with_trailing_slash(self):
        url = "https://moxfield.com/decks/abc-123/"
        assert DeckUrl(url).value == "abc-123"

    def test_accept_only_id(self):
        assert DeckUrl("abc-123").value == "abc-123"

    def test_accept_id_with_numbers_and_hyphens(self):
        assert DeckUrl("deck-123-abc").value == "deck-123-abc"

    def test_accept_id_with_underscores(self):
        assert DeckUrl("deck_123_abc").value == "deck_123_abc"

    def test_raise_for_empty_url(self):
        with pytest.raises(ValueError, match="obrigatória"):
            DeckUrl("")

    def test_raise_for_invalid_url_without_id(self):
        with pytest.raises(ValueError, match="ID de deck"):
            DeckUrl("https://moxfield.com/")

    def test_accept_url_with_query_params(self):
        url = "https://moxfield.com/decks/abc123?format=commander"
        assert DeckUrl(url).value == "abc123"

    def test_accept_url_with_hash(self):
        url = "https://moxfield.com/decks/abc123#section"
        assert DeckUrl(url).value == "abc123"

    def test_case_insensitive_domain(self):
        url = "https://MOXFIELD.COM/decks/abc123"
        assert DeckUrl(url).value == "abc123"

    def test_preserve_id_case(self):
        assert DeckUrl("ABC-123").value == "ABC-123"

    def test_accept_http(self):
        url = "http://moxfield.com/decks/abc123"
        assert DeckUrl(url).value == "abc123"

    def test_reject_url_from_other_domain(self):
        with pytest.raises(ValueError, match="Moxfield"):
            DeckUrl("https://other-site.com/decks/abc123")

    def test_reject_whitespace_only(self):
        with pytest.raises(ValueError, match="obrigatória"):
            DeckUrl("   ")

    def test_reject_overly_long_id(self):
        long_id = "a" * 200
        with pytest.raises(ValueError, match="muito longo"):
            DeckUrl(long_id)

    def test_reject_overly_long_url(self):
        url = "a" * 3000
        with pytest.raises(ValueError, match="muito longa"):
            DeckUrl(url)

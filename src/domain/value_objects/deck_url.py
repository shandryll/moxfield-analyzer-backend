import re
from urllib.parse import urlparse

DECK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
MAX_URL_LENGTH = 2048
MAX_ID_LENGTH = 128


class DeckUrl:
    def __init__(self, url: str) -> None:
        self._value = self._validate(url)

    @property
    def value(self) -> str:
        return self._value

    @staticmethod
    def _validate(url: str) -> str:
        if not url or not url.strip():
            raise ValueError("URL do deck é obrigatória")

        url = url.strip()

        if len(url) > MAX_URL_LENGTH:
            raise ValueError(f"URL muito longa (máximo {MAX_URL_LENGTH} caracteres)")

        if DECK_ID_PATTERN.match(url):
            if len(url) > MAX_ID_LENGTH:
                raise ValueError(f"ID do deck muito longo (máximo {MAX_ID_LENGTH} caracteres)")
            return url

        parsed = urlparse(url)
        if parsed.netloc and "moxfield.com" not in parsed.netloc.lower():
            raise ValueError("URL deve ser do Moxfield")

        match = re.search(r"/decks/([a-zA-Z0-9_-]+)", parsed.path)
        if not match:
            raise ValueError("URL não contém um ID de deck válido")

        deck_id = match.group(1)
        if len(deck_id) > MAX_ID_LENGTH:
            raise ValueError(f"ID do deck muito longo (máximo {MAX_ID_LENGTH} caracteres)")
        return deck_id

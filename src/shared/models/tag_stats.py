from pydantic import BaseModel


class TagStats(BaseModel):
    total: int = 0
    cards: list[str] = []

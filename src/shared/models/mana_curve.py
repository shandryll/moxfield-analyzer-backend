from pydantic import BaseModel


class ManaCurveEntry(BaseModel):
    cmc: int
    count: int

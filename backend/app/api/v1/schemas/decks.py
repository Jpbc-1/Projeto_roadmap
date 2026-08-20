from pydantic import BaseModel, Field


class DeckCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class DeckOut(BaseModel):
    id: int
    name: str
    is_main: bool
    active_count: int
    pending_count: int
    graduated_count: int

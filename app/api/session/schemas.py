import uuid

from pydantic import BaseModel


class ResponseModel(BaseModel):
    type: str
    player_id: uuid.UUID
    detail: dict


class EntityData(BaseModel):
    size: int
    cells: list[int]


class Entities(BaseModel):
    entities: dict[uuid.UUID, EntityData]


class ReadyResponse(Entities):
    board: str

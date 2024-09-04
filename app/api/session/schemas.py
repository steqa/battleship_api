from typing import Literal
from uuid import UUID

from pydantic import field_validator

from api.schemas import BaseSchema
from api.session.exceptions import (
    HttpInvalidNameLength,
    HttpInvalidPasswordLength
)


class Session(BaseSchema):
    id: UUID
    name: str


class SessionCreate(BaseSchema):
    name: str
    password: str

    @field_validator('name')
    def validate_name(cls, name):
        if len(name) < 1:
            raise HttpInvalidNameLength
        return name

    @field_validator('password')
    def validate_password(cls, password):
        if len(password) < 1:
            raise HttpInvalidPasswordLength
        return password


class SessionLogin(SessionCreate):
    ...


class PlayerIDResponse(BaseSchema):
    player_id: UUID


class WsMessageModel(BaseSchema):
    type: str
    detail: dict


class EntityCells(BaseSchema):
    cells: list[int]


class EntityData(EntityCells):
    size: int
    direction: int


class Entities(BaseSchema):
    entities: dict[UUID, EntityData]

    def to_dict(self):
        return {
            'entities': {
                str(uuid): entity.model_dump() for uuid, entity in self.entities.items()
            }
        }


class PlayerPlacement(Entities):
    board: str


class Hit(BaseSchema):
    cell: int
    entity_id: str


class HitResponse(Hit):
    status: Literal['hit', 'miss', 'destroy']

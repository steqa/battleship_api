import json
import logging

import pydantic
from fastapi import WebSocket

from api.session.schemas import (
    WsMessageModel,
    PlayerPlacement,
    Hit
)
from api.session.websocket_response_types import WsResponseType

logger = logging.getLogger(__name__)


async def ws_receive_player_start_session_message(websocket: WebSocket) -> dict:
    return await ws_receive_message_by_type(websocket, WsResponseType.PLAYER_START_SESSION)


async def ws_receive_player_placement_ready_message(websocket: WebSocket) -> PlayerPlacement:
    while True:
        message = await ws_receive_message_by_type(websocket, WsResponseType.PLAYER_PLACEMENT_READY)
        try:
            detail = PlayerPlacement(**message)
            return detail
        except pydantic.ValidationError:
            logger.warning('Invalid player placement message format!')


async def ws_receive_player_hit_message(websocket: WebSocket) -> Hit:
    while True:
        message = await ws_receive_message_by_type(websocket, WsResponseType.HIT)
        try:
            detail = Hit(**message)
            if detail.cell < 0 or detail.cell > 99:
                raise pydantic.ValidationError
            return detail
        except pydantic.ValidationError:
            logger.warning('Invalid player hit message format!')


async def ws_receive_message_by_type(
        websocket: WebSocket,
        message_type: WsResponseType
) -> dict:
    while True:
        message = await ws_receive_message(websocket)
        if message.type == message_type:
            return message.detail


async def ws_receive_message(websocket: WebSocket) -> WsMessageModel:
    while True:
        data = await websocket.receive_text()
        logger.debug('Received data:\n%s', data)
        try:
            json_message = json.loads(data)
            message = WsMessageModel(**json_message)
            return message
        except json.decoder.JSONDecodeError:
            logger.warning('Data is invalid JSON!')
        except pydantic.ValidationError:
            logger.warning('Invalid JSON format!')

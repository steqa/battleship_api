import json
import logging

import pydantic
from fastapi import WebSocket

from api.session.exceptions import (
    WsJsonDecodeException,
    WsInvalidJsonFormat
)
from api.session.response_types import WsMessageType
from api.session.schemas import (
    WsMessageModel,
)

logger = logging.getLogger(__name__)


async def ws_receive_player_start_game_message(websocket: WebSocket) -> dict:
    return await ws_receive_message_by_type(websocket, WsMessageType.player_start_game)


async def ws_receive_message_by_type(
        websocket: WebSocket,
        message_type: WsMessageType
) -> dict:
    while True:
        message = await ws_receive_message(websocket)
        if message.type == message_type:
            return message.detail


async def ws_receive_message(websocket: WebSocket) -> WsMessageModel:
    data = await websocket.receive_text()
    logger.debug('Received data:\n%s', data)
    try:
        json_message = json.loads(data)
        message = WsMessageModel(**json_message)
    except json.decoder.JSONDecodeError:
        logger.warning('Data is invalid JSON!')
        raise WsJsonDecodeException
    except pydantic.ValidationError:
        logger.warning('Invalid JSON format!')
        raise WsInvalidJsonFormat
    return message

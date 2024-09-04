import logging
import random
from typing import Literal
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from api.session import services
from api.session.exceptions import (
    WsPlayerNotFound
)
from api.session.redis_services import (
    get_player_board,
    add_player_hits,
    add_entity_hits,
    get_entity_size
)
from api.session.schemas import (
    Entities,
    HitResponse
)
from api.session.utils import check_full_board_in_hits
from api.session.websocket_request_types import WsRequestType
from api.session.websocket_response_types import WsResponseType
from api.session.websocket_utils import (
    ws_receive_player_start_session_message,
    ws_receive_message,
    ws_receive_player_hit_message,
)

logger = logging.getLogger(__name__)


class Player:
    __slots__ = ('websocket', 'enemy_joined', 'is_ready', 'turn')

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        self.enemy_joined = False
        self.is_ready = False
        self.turn = False


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, Player] = {}

    async def connect(self, websocket: WebSocket, player_id: UUID):
        await websocket.accept()
        self.active_connections[player_id] = Player(websocket)
        logger.debug('Websocket connected, player_id: %s', player_id)

    async def disconnect(self, player_id: UUID):
        connection = self.active_connections.pop(player_id, None)
        if connection:
            if connection.websocket.client_state != WebSocketState.DISCONNECTED:
                await connection.websocket.close()
            logger.debug('Websocket disconnected, player_id: %s', player_id)

    async def login_session(
            self,
            websocket: WebSocket,
            session_id: UUID,
            player_id: UUID,
    ) -> None:
        enemy = await services.get_enemy(player_id, session_id)
        if enemy is not None and enemy.id in self.active_connections:
            await self.send_enemy_joined_message(to_id=player_id)
            await self.send_enemy_joined_message(to_id=enemy.id)
            self.active_connections[player_id].enemy_joined = True
            self.active_connections[enemy.id].enemy_joined = True

            await ws_receive_player_start_session_message(websocket)
            await self.send_start_session_message(to_id=player_id)
            logger.debug('Session start, player_id: %s', player_id)
        else:
            await ws_receive_player_start_session_message(websocket)
            if self.active_connections[player_id].enemy_joined:
                await self.send_start_session_message(to_id=player_id)
                logger.debug('Session start, player_id: %s', player_id)

    async def start_game(
            self,
            websocket: WebSocket,
            player_id: UUID,
            enemy_id: UUID
    ) -> bool:
        logger.debug('Player is ready, player_id: %s', player_id)
        self.active_connections[player_id].is_ready = True
        enemy_is_ready = self.active_connections[enemy_id].is_ready
        if enemy_is_ready:
            await self.send_enemy_placement_ready_message(to_id=player_id)
            await self.send_enemy_placement_ready_message(to_id=enemy_id)
            turn = random.choice([True, False])
            self.active_connections[player_id].turn = turn
            self.active_connections[enemy_id].turn = not turn

        while True:
            message = await ws_receive_message(websocket)
            enemy_is_ready = self.active_connections[enemy_id].is_ready
            if message.type == WsResponseType.PLAYER_START_GAME and enemy_is_ready:
                await self.send_start_game_message(to_id=player_id)
                logger.debug('Game start, player_id: %s', player_id)
                return True
            elif message.type == WsResponseType.PLAYER_PLACEMENT_NOT_READY and not enemy_is_ready:
                logger.debug('Player is not ready, player_id: %s', player_id)
                self.active_connections[player_id].is_ready = False
                break

    async def handle_hit(
            self,
            websocket: WebSocket,
            session_id: UUID,
            player_id: UUID,
            enemy_id: UUID
    ) -> None:
        if self.active_connections[player_id].turn is True:
            await self.send_your_turn_message(to_id=player_id)
            logger.debug('Turn, player_id: %s', player_id)

        message = await ws_receive_player_hit_message(websocket)
        if self.active_connections[player_id].turn is False:
            return
        response_data = {
            'player_id': player_id,
            'enemy_id': enemy_id,
            'cell': message.cell,
            'entity_id': message.entity_id
        }
        board = await get_player_board(session_id, enemy_id)
        hits = await add_player_hits(session_id, enemy_id, message.cell)
        if board[message.cell] == '0':
            await self.send_hit_response_to_players(**response_data, status='miss')
        else:
            if check_full_board_in_hits(board, hits):
                await self.send_hit_response_to_players(**response_data, status='destroy')
                await self.send_win_message(to_id=player_id)
                await self.send_defeat_message(to_id=enemy_id)
            else:
                entity_hits = await add_entity_hits(
                    session_id,
                    enemy_id,
                    message.entity_id,
                    1
                )
                entity_size = await get_entity_size(
                    session_id,
                    enemy_id,
                    message.entity_id
                )
                if entity_hits >= entity_size:
                    await self.send_hit_response_to_players(**response_data, status='destroy')
                else:
                    await self.send_hit_response_to_players(**response_data, status='hit')

        self.active_connections[player_id].turn = not self.active_connections[player_id].turn
        self.active_connections[enemy_id].turn = not self.active_connections[player_id].turn
        await self.send_your_turn_message(to_id=enemy_id)
        logger.debug('Turn, player_id: %s', enemy_id)

    async def send_enemy_joined_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.ENEMY_JOINED)

    async def send_enemy_left_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.ENEMY_LEFT)

    async def send_start_session_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.START_SESSION)

    async def send_enemy_placement_ready_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.ENEMY_PLACEMENT_READY)

    async def send_start_game_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.START_GAME)

    async def send_your_turn_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.YOUR_TURN)

    async def send_player_entities_message(
            self,
            to_id: UUID,
            entities: Entities
    ) -> None:
        detail = entities.to_dict()
        await self.__send_message(to_id, WsRequestType.ENEMY_ENTITIES, detail)

    async def send_hit_response_to_players(
            self,
            player_id: UUID,
            enemy_id: UUID,
            cell: int,
            entity_id: str,
            status: Literal['hit', 'miss', 'destroy']
    ) -> None:
        detail = HitResponse(
            cell=cell,
            entity_id=entity_id,
            status=status
        ).model_dump(by_alias=True)
        await self.__send_message(player_id, WsRequestType.PLAYER_HIT, detail)
        await self.__send_message(enemy_id, WsRequestType.ENEMY_HIT, detail)

    async def send_win_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.WIN)

    async def send_defeat_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.DEFEAT)

    async def __send_message(
            self,
            player_id: UUID,
            message_type: WsRequestType,
            detail: dict | str | None = None
    ) -> None:
        if player_id not in self.active_connections:
            logger.warning('Player for message not found, player_id: %s', player_id)
            raise WsPlayerNotFound
        connection = self.active_connections[player_id].websocket
        if connection.client_state == WebSocketState.CONNECTED:
            if detail is None:
                detail = {}
            message = {"type": message_type, "detail": detail}
            await connection.send_json(message)
            logger.debug('Message sent to player, player_id: %s, message:\n%s', player_id, message)
        else:
            logger.warning('Cannot send message to disconnected websocket, player_id: %s', player_id)


manager = ConnectionManager()

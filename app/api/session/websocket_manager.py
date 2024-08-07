import json
import logging
from dataclasses import dataclass
from uuid import uuid4, UUID

from fastapi import WebSocket

from api.session import services
from api.session.exceptions import PlayerNotFound, SessionAlreadyFull
from api.session.websocket_messages import (
    player_id_message,
    enemy_id_message,
    enemy_left_message,
    game_is_ready
)

logger = logging.getLogger(__name__)


@dataclass
class Player:
    uuid: UUID
    websocket: WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, list[Player]] = {}

    async def connect(self, websocket: WebSocket, name: str, password: str) -> [UUID, UUID]:
        logger.debug('Connect to session: %s', name)
        session = await services.get_session(name=name, password=password)

        if session is not None and session.player2_id is not None:
            logger.warning('Session already full!')
            raise SessionAlreadyFull

        await websocket.accept()
        logger.debug('WebSocket connected.')

        new_player = Player(uuid=uuid4(), websocket=websocket)
        if session is None:
            session = await services.create_session(name, password, new_player.uuid)
            logger.info('Session created in database with player1_id: %s', new_player.uuid)
        else:
            session = await services.update_session(session.id, new_player2_id=new_player.uuid)
            logger.info('Session updated in database with player2_id: %s', new_player.uuid)

        self.active_connections.setdefault(session.id, []).append(new_player)
        logger.debug('Session connected, session_id: %s, player_id: %s', session.id, new_player.uuid)
        return session.id, new_player.uuid

    async def disconnect(self, session_id: UUID, player_id: UUID):
        connections = self.active_connections
        if session_id in connections:
            session = connections[session_id]
            player = await self.__get_player(session_id, player_id)
            if player is not None:
                session.remove(player)
                logger.info('Player disconnected from session, player_id: %s, session_id: %s', player_id, session_id)

            enemy = await self.__get_enemy(session_id, player_id)
            if enemy is None:
                logger.debug('Session is empty.')
                await self.delete_connections(session_id)
                await services.delete_session(uuid=session_id)
                logger.info('Session deleted from database.')
            else:
                message = enemy_left_message()
                await self.__send_message(enemy, message)
                logger.debug("Player's exit message sent to enemy.")

    async def delete_connections(self, session_id: UUID) -> None:
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_player_id(self, session_id, player_id) -> None:
        message = player_id_message(player_id)
        await self.send_message_to_player(session_id, player_id, message)
        logger.debug('Player ID sent.')

    async def send_enemies_id(self, session_id: UUID) -> None:
        players = self.active_connections[session_id]
        for player in players:
            enemy = await self.__get_enemy(session_id, player.uuid)
            message = enemy_id_message(enemy.uuid)
            await manager.__send_message(player, message)
            logger.debug("Enemies ID's sent.")

    async def send_game_is_ready(self, session_id: UUID) -> None:
        players = self.active_connections[session_id]
        for player in players:
            await manager.__send_message(player, game_is_ready())

    async def send_message_to_player(self, session_id: UUID, player_id: UUID, message: dict):
        player = await self.__get_player(session_id, player_id)
        await self.__send_message(player, message)

    async def send_message_to_enemy(self, session_id: UUID, player_id: UUID, message: dict):
        enemy = await self.__get_enemy(session_id, player_id)
        await self.__send_message(enemy, message)

    async def session_is_ready(self, session_id: UUID) -> bool:
        connections = self.active_connections
        if (session_id in connections) and (len(connections[session_id]) == 2):
            return True
        return False

    async def __get_player(self, session_id: UUID, player_id: UUID) -> Player | None:
        players = self.active_connections[session_id]
        for player in players:
            if player.uuid == player_id:
                return player
        return None

    async def __get_enemy(self, session_id: UUID, player_id: UUID) -> Player | None:
        players = self.active_connections[session_id]
        for player in players:
            if player.uuid != player_id:
                return player
        return None

    @staticmethod
    async def __send_message(player: Player, message: dict) -> None:
        if player is None:
            logger.warning('Player for message not found!')
            raise PlayerNotFound
        await player.websocket.send_text(json.dumps(message))
        logger.debug('Message sent to player, player_id: %s, message: %s', player.uuid, message)


manager = ConnectionManager()

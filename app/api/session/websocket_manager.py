import json
from uuid import uuid4, UUID
from fastapi import WebSocket, WebSocketException, status
from api.session import services
from dataclasses import dataclass
from api.session.websocket_messages import (
    player_id_message,
    enemy_id_message,
    enemy_left_message
)


@dataclass
class Player:
    uuid: UUID
    websocket: WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_sessions: dict[UUID, list[Player]] = {}

    async def connect(self, websocket: WebSocket, name: str, password: str) -> [UUID, UUID]:
        session = await services.get_session(name, password)

        if session is not None and session.player2_id is not None:
            raise WebSocketException(code=status.HTTP_403_FORBIDDEN)
        await websocket.accept()

        new_player = Player(uuid=uuid4(), websocket=websocket)
        if session is None:
            session = await services.create_session(name, password, new_player.uuid)
        else:
            session = await services.update_session(session.id, new_player2_id=new_player.uuid)

        self.active_sessions.setdefault(session.id, []).append(new_player)
        return session.id, new_player.uuid

    async def disconnect(self, session_id: UUID, player_id: UUID):
        sessions = self.active_sessions
        if session_id in sessions:
            session = sessions[session_id]
            player = await self.__get_player(session_id, player_id)
            if player is not None:
                session.remove(player)

            enemy = await self.__get_enemy(session_id, player_id)
            if enemy is None:
                del sessions[session_id]
                await services.delete_session(uuid=session_id)
            else:
                message = enemy_left_message()
                await self.__send_message(enemy, message)

    async def send_player_id(self, session_id, player_id) -> None:
        message = player_id_message(player_id)
        await self.send_message_to_player(session_id, player_id, message)

    async def send_enemies_id(self, session_id: UUID) -> None:
        if await manager.__session_is_ready(session_id):
            session = self.active_sessions[session_id]
            for player in session:
                enemy = await self.__get_enemy(session_id, player.uuid)
                message = enemy_id_message(enemy.uuid)
                await manager.__send_message(player, message)

    async def send_message_to_player(self, session_id: UUID, player_id: UUID, message: dict):
        player = await self.__get_player(session_id, player_id)
        await self.__send_message(player, message)

    async def send_message_to_enemy(self, session_id: UUID, player_id: UUID, message: dict):
        enemy = await self.__get_enemy(session_id, player_id)
        await self.__send_message(enemy, message)

    async def __session_is_ready(self, session_id: UUID) -> bool:
        sessions = self.active_sessions
        if (session_id in sessions) and (len(sessions[session_id]) == 2):
            return True
        return False

    async def __get_player(self, session_id: UUID, player_id: UUID) -> Player | None:
        session = self.active_sessions[session_id]
        for player in session:
            if player.uuid == player_id:
                return player
        return None

    async def __get_enemy(self, session_id: UUID, player_id: UUID) -> Player | None:
        session = self.active_sessions[session_id]
        for player in session:
            if player.uuid != player_id:
                return player
        return None

    @staticmethod
    async def __send_message(player: Player, message: dict) -> None:
        if player is None:
            raise WebSocketException(code=status.HTTP_404_NOT_FOUND)
        await player.websocket.send_text(json.dumps(message))


manager = ConnectionManager()

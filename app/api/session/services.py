import logging
from uuid import UUID

from sqlalchemy import select, insert, delete, desc, update

from api.services import execute_query
from api.session.models import session, player
from api.session.utils import hash_password

logger = logging.getLogger(__name__)


async def create_session(name: str, password: str) -> session:
    hashed_password = hash_password(password)
    query = insert(session).values([{
        'name': name,
        'password': hashed_password,
    }]).returning(session)
    return await execute_query(query, commit=True)


async def get_sessions(desc_sort: bool = False) -> session:
    query = select(session)
    if desc_sort is True:
        query = query.order_by(desc(session.c.created_at))
    return await execute_query(query, first_only=False)


async def get_session(
        uuid: UUID = None,
        name: str = None,
        password: str = None
) -> session:
    query = select(session)
    if uuid is not None:
        query = query.where(session.c.id == uuid)
    if name is not None:
        query = query.where(session.c.name == name)
    if password is not None:
        query = query.where(session.c.password == password)
    return await execute_query(query)


async def update_session(
        uuid: UUID,
        name: str = None,
        password: str = None,
        is_ready: bool = None
) -> session:
    query = update(session).where(session.c.id == uuid)
    values = {}
    if name is not None:
        values['name'] = name
    if password is not None:
        values['password'] = password
    if is_ready is not None:
        values['is_ready'] = is_ready
    query = query.values(values).returning(session)
    return await execute_query(query, commit=True)


async def delete_session(uuid: UUID) -> None:
    query = delete(session).where(session.c.id == uuid)
    await execute_query(query, commit=True, return_result=False)


async def create_player(session_id: UUID) -> player:
    query = insert(player).values([{
        'session_id': session_id,
    }]).returning(player)
    return await execute_query(query, commit=True)


async def get_player(uuid: UUID) -> player:
    query = select(player).where(player.c.id == uuid)
    return await execute_query(query, commit=True)


async def update_player(
        uuid: UUID,
        session_id: UUID = None,
) -> player:
    query = update(player).where(player.c.id == uuid)
    values = {}
    if session_id is not None:
        values['session_id'] = session_id
    query = query.values(values).returning(player)
    return await execute_query(query, commit=True)


async def delete_player(uuid: UUID) -> None:
    query = delete(player).where(player.c.id == uuid)
    await execute_query(query, commit=True, return_result=False)


async def get_enemy(player_id: UUID, session_id: UUID) -> player:
    query = select(player).where(
        player.c.id != player_id,
        player.c.session_id == session_id
    )
    return await execute_query(query, commit=True)
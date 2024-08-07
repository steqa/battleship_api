from uuid import UUID

from sqlalchemy import select, update, insert, delete

from api.services import execute_query
from api.session.models import session


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


async def create_session(name: str, password: str, player1_id: UUID) -> session:
    query = insert(session).values([{
        'name': name,
        'password': password,
        'player1_id': player1_id
    }]).returning(session)
    return await execute_query(query, commit=True)


async def update_session(
        uuid: UUID,
        new_name: str = None,
        new_password: str = None,
        new_player1_id: UUID = None,
        new_player1_ready: bool = None,
        new_player2_id: UUID = None,
        new_player2_ready: bool = None
) -> session:
    query = update(session).where(session.c.id == uuid)
    values = {}
    if new_name is not None:
        values['name'] = new_name
    if new_password is not None:
        values['password'] = new_password
    if new_player1_id is not None:
        values['player1_id'] = new_player1_id
    if new_player1_ready is not None:
        values['player1_ready'] = new_player1_ready
    if new_player2_id is not None:
        values['player2_id'] = new_player2_id
    if new_player2_ready is not None:
        values['player2_ready'] = new_player2_ready
    query = query.values(values).returning(session)
    return await execute_query(query, commit=True)


async def delete_session(uuid: UUID) -> None:
    query = delete(session).where(session.c.id == uuid)
    await execute_query(query, commit=True, return_result=False)

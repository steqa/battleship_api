from sqlalchemy import select, update, insert, delete
from api.session.models import session
from api.services import execute_query
from uuid import UUID


async def get_session(name: str, password: str) -> session:
    query = select(session).where(
        session.c.name == name,
        session.c.password == password
    )
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
        new_player2_id: UUID = None
) -> session:
    query = update(session).where(session.c.id == uuid)
    values = {}
    if new_name is not None:
        values['name'] = new_name
    if new_password is not None:
        values['password'] = new_password
    if new_player1_id is not None:
        values['player1_id'] = new_player1_id
    if new_player2_id is not None:
        values['player2_id'] = new_player2_id
    query = query.values(values).returning(session)
    return await execute_query(query, commit=True)


async def delete_session(uuid: UUID) -> None:
    query = delete(session).where(session.c.id == uuid)
    await execute_query(query, commit=True, return_result=False)

from uuid import UUID

import redis.asyncio as redis

from api.config import settings
from api.session.schemas import EntityData

REDIS_URL = f'redis://redis:{settings.REDIS_PORT}'


async def set_player_data(
        session_id: UUID,
        player_id: UUID,
        board: str,
        entities: dict[UUID, EntityData]
) -> None:
    client = redis.from_url(REDIS_URL)

    await client.hset(
        f'session:{session_id}',
        f'player:{player_id}:board',
        board
    )
    await client.hset(
        f'session:{session_id}',
        f'player:{player_id}:hits',
        '0' * settings.GRID_SIZE_X * settings.GRID_SIZE_Y
    )

    for entity_id, entity_data in entities.items():
        await client.hset(
            f'session:{session_id}',
            f'player:{player_id}:entity:{entity_id}:hits',
            0
        )
        await client.hset(
            f'session:{session_id}',
            f'player:{player_id}:entity:{entity_id}:size',
            entity_data.size
        )
        await client.hset(
            f'session:{session_id}',
            f'player:{player_id}:entity:{entity_id}:direction',
            entity_data.direction
        )
        await client.hset(
            f'session:{session_id}',
            f'player:{player_id}:entity:{entity_id}:cells',
            ' '.join(str(cell) for cell in entity_data.cells)
        )

    await client.close()


async def get_player_board(session_id: UUID, player_id: UUID) -> str:
    client = redis.from_url(REDIS_URL)
    board = await client.hget(
        f'session:{session_id}',
        f'player:{player_id}:board'
    )
    await client.close()
    return board.decode('utf-8')


async def get_entity_size(session_id: UUID, player_id: UUID, entity_id: str) -> int:
    client = redis.from_url(REDIS_URL)
    size = await client.hget(
        f'session:{session_id}',
        f'player:{player_id}:entity:{entity_id}:size'
    )
    await client.close()
    return int(size.decode('utf-8'))


async def add_player_hits(session_id: UUID, player_id: UUID, cell: int) -> str:
    client = redis.from_url(REDIS_URL)
    hits = await client.hget(
        f'session:{session_id}',
        f'player:{player_id}:hits'
    )
    hits_str = str(hits.decode('utf-8'))
    new_hits = hits_str[0:cell] + '1' + hits_str[cell+1:]
    await client.hset(
        f'session:{session_id}',
        f'player:{player_id}:hits',
        new_hits
    )
    await client.close()
    return new_hits


async def add_entity_hits(
        session_id: UUID,
        player_id: UUID,
        entity_id: str,
        count: int
) -> int:
    client = redis.from_url(REDIS_URL)
    hits = await client.hget(
        f'session:{session_id}',
        f'player:{player_id}:entity:{entity_id}:hits'
    )
    new_hits = int(hits.decode('utf-8')) + count
    await client.hset(
        f'session:{session_id}',
        f'player:{player_id}:entity:{entity_id}:hits',
        new_hits
    )
    await client.close()
    return new_hits


async def delete_session(session_id: UUID) -> None:
    client = redis.from_url(REDIS_URL)
    await client.delete(f'session:{session_id}')
    await client.close()

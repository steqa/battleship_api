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
        '0' * 10 * 10
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


async def delete_session(session_id: UUID) -> None:
    client = redis.from_url(REDIS_URL)
    await client.delete(f'session:{session_id}')
    await client.close()

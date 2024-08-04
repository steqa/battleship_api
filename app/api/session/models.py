from sqlalchemy import Table, Column, String, UUID, text
from api.database import metadata


session = Table(
    'session', metadata,
    Column('id', UUID, primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
    Column('name', String, nullable=False),
    Column('password', String, nullable=False),
    Column('player1_id', UUID),
    Column('player2_id', UUID),
)
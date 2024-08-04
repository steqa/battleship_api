from api.database import engine


async def execute_query(
        query,
        commit: bool = False,
        return_result: bool = True,
        first_only: bool = True
):
    async with engine.connect() as connection:
        result = await connection.execute(query)
        if commit is True:
            await connection.commit()
        if return_result is True:
            if first_only is True:
                return result.fetchone()
            return result.fetchall()

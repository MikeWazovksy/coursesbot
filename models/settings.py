import asyncpg

async def get_setting(pool: asyncpg.Pool, key: str) -> str | None:
    query = "SELECT value FROM settings WHERE key = $1"
    result = await pool.fetchval(query, key)
    return result


async def set_setting(pool: asyncpg.Pool, key: str, value: str):
    query = """
        INSERT INTO settings (key, value)
        VALUES ($1, $2)
        ON CONFLICT (key) DO UPDATE
        SET value = EXCLUDED.value;
    """
    await pool.execute(query, key, value)

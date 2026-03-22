"""
Migration: add sortOrder column to cards table.
Run once in Render shell:
  python -c "import asyncio; from app.migrate_sort_order import run; asyncio.run(run())"
"""
import asyncio
from sqlalchemy import text
from app.db.conection import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(
            text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS "sortOrder" INTEGER')
        )
    print("Migration complete: sortOrder column added to cards.")


if __name__ == "__main__":
    asyncio.run(run())

"""
Migration: fix is_final flags and completed_at for existing data.

Run once from the Back-end/ directory:
    python fix_final_lists.py
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.conection import Session
# Import all models so SQLAlchemy resolves all relationships
import app.db.models.__all_models  # noqa: F401
from app.db.models.card_model import CardModel
from app.db.models.list_model import ListModel
from app.db.models.project_model import ProjectModel


async def fix():
    async with Session() as session:
        # Get all project IDs
        project_ids = (
            await session.execute(select(ProjectModel.id))
        ).scalars().all()

        for pid in project_ids:
            lists_result = await session.execute(
                select(ListModel)
                .where(ListModel.project_id == pid)
                .order_by(ListModel.order.desc())
            )
            lists = lists_result.unique().scalars().all()

            if not lists:
                continue

            final_list = lists[0]
            print(f"Project {pid}: final list = '{final_list.name}' (id={final_list.id})")

            for i, lst in enumerate(lists):
                lst.is_final = i == 0

            await session.flush()

            non_final_ids = [lst.id for lst in lists[1:]]
            if non_final_ids:
                await session.execute(
                    update(CardModel)
                    .where(CardModel.list_id.in_(non_final_ids))
                    .values(completed_at=None)
                )

            await session.execute(
                update(CardModel)
                .where(
                    CardModel.list_id == final_list.id,
                    CardModel.completed_at.is_(None),
                )
                .values(completed_at=CardModel.created_at)  # use created_at as fallback
            )

        await session.commit()
        print("Done! is_final and completed_at fixed for all projects.")


asyncio.run(fix())

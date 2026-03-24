from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_current_user, get_session
from app.db.models.category_model import CategoryModel
from app.schemas.category_schema import CategorySchema
from app.schemas.user_schema import UserSchema

router = APIRouter()


@router.get("/", response_model=list[CategorySchema])
async def list_categories(
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Returns all available card categories ordered by name."""
    result = await db_session.execute(
        select(CategoryModel).order_by(CategoryModel.name)
    )
    return result.scalars().all()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.core.deps import get_current_user, get_session
from app.schemas.comment_schema import (
    CommentCreateSchema,
    CommentSchema,
    CommentSchemaBase,
)
from app.schemas.user_schema import UserSchema
from app.rules.comments import CommentRules

router = APIRouter()


@router.post(
    "/card/{card_id}", response_model=CommentSchema, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    card_id: int,
    comment_data: CommentCreateSchema,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = CommentRules(db_session)
    try:
        comment = await rules.add_comment(card_id, comment_data, current_user.id)
        return comment
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{comment_id}", response_model=CommentSchema)
async def update_comment(
    comment_id: int,
    comment_update: CommentSchemaBase,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = CommentRules(db_session)
    try:
        comment = await rules.update_comment(
            comment_id, comment_update.description, current_user.id
        )
        return comment
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = CommentRules(db_session)
    try:
        await rules.delete_comment(comment_id, current_user.id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

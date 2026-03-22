from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.schemas.list_schema import ListSchema, ListSchemaSlim, ListSchemaUp
from app.schemas.card_schema import CardPageResponse
from app.core.deps import get_session, get_current_user
from app.rules.list import ListRules
from app.schemas.user_schema import UserSchema

router = APIRouter()


@router.get("/", response_model=list[ListSchemaSlim])
async def get_lists(
    project_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ListRules(db)
    return await rules.get_lists_slim(project_id)


@router.get("/{list_id}/cards", response_model=CardPageResponse)
async def get_cards_for_list(
    project_id: int,
    list_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=2000),
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ListRules(db)
    return await rules.get_cards_for_list_paginated(list_id, page, limit)


@router.post("/", response_model=ListSchema, status_code=status.HTTP_201_CREATED)
async def create_list(
    project_id: int,
    data: ListSchemaUp,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ListRules(db)
    try:
        return await rules.add_list(project_id, data, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{list_id}", response_model=ListSchema)
async def update_list(
    project_id: int,
    list_id: int,
    data: ListSchemaUp,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ListRules(db)
    try:
        return await rules.update_list(project_id, list_id, data, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NoResultFound:
        raise HTTPException(status_code=404, detail="List not found")


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    project_id: int,
    list_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ListRules(db)
    try:
        await rules.delete_list(project_id, list_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NoResultFound:
        raise HTTPException(status_code=404, detail="List not found")

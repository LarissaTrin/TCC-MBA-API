from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel as PydanticBaseModel

from app.schemas.user_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserSchemaCreate,
    UserSchemaUp,
    UserSchema,
    TokenData,
)


class NotesBody(PydanticBaseModel):
    notes: str
from app.core.deps import get_current_user, get_session
from app.rules.user import UserRules
from app.db.models.user_model import UserModel
from app.db.models.user_notes_model import UserNotesModel

router = APIRouter()


@router.post("/login", response_model=TokenData)
async def login(
    login_data: OAuth2PasswordRequestForm = Depends(),
    db_session: AsyncSession = Depends(get_session),
):
    rules = UserRules(db_session)
    token_data = await rules.login(login_data.username, login_data.password)
    return token_data


@router.post("/", response_model=TokenData, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserSchemaCreate,
    db_session: AsyncSession = Depends(get_session),
):
    rules = UserRules(db_session)
    await rules.create_user(user_data)
    token_data = await rules.login(user_data.email, user_data.password)
    return token_data


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    data: UserSchemaUp,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    rules = UserRules(db_session)
    user = await rules.update_user(user_id, current_user.id, data)
    return user


@router.get("/user", response_model=UserSchema)
async def get_current_user_info(
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    rules = UserRules(db_session)
    user = await rules.get_user_by_id(current_user.id, current_user.id)
    return UserSchema.model_validate(user)


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    rules = UserRules(db_session)
    user = await rules.get_user_by_id(user_id, current_user.id)
    return user


@router.get("/me/notes")
async def get_notes(
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy.future import select
    result = await db_session.execute(
        select(UserNotesModel).where(UserNotesModel.user_id == current_user.id)
    )
    notes_row = result.scalar_one_or_none()
    return {"notes": notes_row.content if notes_row else ""}


@router.put("/me/notes")
async def save_notes(
    body: NotesBody,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy.future import select
    result = await db_session.execute(
        select(UserNotesModel).where(UserNotesModel.user_id == current_user.id)
    )
    notes_row = result.scalar_one_or_none()
    if notes_row:
        notes_row.content = body.notes
    else:
        db_session.add(UserNotesModel(user_id=current_user.id, content=body.notes))
    await db_session.commit()
    return {"notes": body.notes}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db_session: AsyncSession = Depends(get_session),
):
    rules = UserRules(db_session)
    await rules.forgot_password(data.email)
    return {
        "message": "Se o e-mail existir, você receberá um link para redefinir a senha."
    }


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    rules = UserRules(db_session)
    await rules.reset_password(current_user.id, data.new_password)
    return {"message": "Senha redefinida com sucesso."}

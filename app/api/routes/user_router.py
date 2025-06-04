from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserSchemaCreate,
    UserSchemaUp,
    UserSchema,
    TokenData,
)
from app.core.deps import get_current_user, get_session
from app.rules.user import UserRules
from app.db.models.user_model import UserModel

router = APIRouter()


@router.post("/login", response_model=TokenData)
async def login(
    login_data: OAuth2PasswordRequestForm = Depends(),
    db_session: AsyncSession = Depends(get_session),
):
    rules = UserRules(db_session)
    token_data = await rules.login(login_data.username, login_data.password)
    return token_data


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserSchemaCreate,
    db_session: AsyncSession = Depends(get_session),
):
    rules = UserRules(db_session)
    user = await rules.create_user(user_data)
    return user


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


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    rules = UserRules(db_session)
    user = await rules.get_user_by_id(user_id, current_user.id)
    return user


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

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel as PydanticBaseModel

from app.core.configs import settings
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
    user = await rules.create_user(user_data)
    # Generate token directly — avoids a redundant bcrypt.verify() call that login() would trigger,
    # cutting registration time roughly in half on CPU-limited environments.
    access_token = rules.token_service.create_access_token(sub=user.id)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return TokenData(
        access_token=access_token,
        expires_at=expires_at,
        user_id=user.id,
        first_name=user.firstName,
        last_name=user.lastName,
    )


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
        "message": "If the email exists, you will receive a password reset link."
    }


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db_session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    rules = UserRules(db_session)
    await rules.reset_password(current_user.id, data.new_password)
    return {"message": "Password reset successfully."}

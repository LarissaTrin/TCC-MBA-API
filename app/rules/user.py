from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.email import send_email
from app.core.configs import settings
from app.core.auth import TokenService
from app.core.security import generator_hash_password
from app.db.models.user_model import UserModel
from app.schemas.user_schema import TokenData, UserSchemaCreate, UserSchemaUp


class UserRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.token_service = TokenService()

    async def login(self, email: str, password: str) -> TokenData:
        user = await self.token_service.authenticate(
            email=email, password=password, db=self.db_session
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials.",
            )

        access_token = self.token_service.create_access_token(sub=user.id)

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

    async def create_user(self, user_data: UserSchemaCreate) -> UserModel:
        """
        Creates a new user after checking that the email and username are not taken.

        Args:
            user_data (UserSchemaCreate): Data for the new user.

        Returns:
            UserModel: The newly created user.

        Raises:
            HTTPException: If the email or username already exist.
        """
        # Check email
        email_query = select(UserModel).where(UserModel.email == user_data.email)
        result = await self.db_session.execute(email_query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

        # Check username
        username_query = select(UserModel).where(
            UserModel.username == user_data.username
        )
        result = await self.db_session.execute(username_query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered.",
            )

        new_user = UserModel(
            firstName=user_data.first_name,
            lastName=user_data.last_name,
            email=user_data.email,
            username=user_data.username,
            password=generator_hash_password(user_data.password),
            isAdmin=user_data.is_admin,
        )

        try:
            self.db_session.add(new_user)
            await self.db_session.commit()
            await self.db_session.refresh(new_user)
            return new_user

        except IntegrityError:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating user.",
            )

        except Exception:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error creating user.",
            )

    async def update_user(
        self, user_id: int, current_user_id: int, data: UserSchemaUp
    ) -> UserModel:
        """
        Updates a user's data. Only the authenticated user can edit their own account.

        Args:
            user_id (int): ID of the user to be edited.
            current_user_id (int): ID of the authenticated user.
            data (UserSchemaUp): Fields to update.

        Returns:
            UserModel: The updated user.

        Raises:
            HTTPException: If the user tries to edit someone else's account or there is a data conflict.
        """
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own account.",
            )

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Check if new email is already taken
        if data.email and data.email != user.email:
            email_query = select(UserModel).where(UserModel.email == data.email)
            result = await self.db_session.execute(email_query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="Email already in use by another user.",
                )

        # Update fields
        if data.first_name is not None:
            user.firstName = data.first_name
        if data.last_name is not None:
            user.lastName = data.last_name
        if data.email is not None:
            user.email = data.email
        if data.password is not None:
            user.password = generator_hash_password(data.password)
        if data.is_admin is not None:
            user.isAdmin = data.is_admin

        try:
            await self.db_session.commit()
            await self.db_session.refresh(user)
            return user
        except IntegrityError:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=400,
                detail="Error updating user.",
            )
        except Exception:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unexpected error updating user.",
            )

    async def get_user_by_id(self, user_id: int, current_user_id: int) -> UserModel:
        """
        Fetches a user by ID. Only the authenticated user can access their own data.

        Args:
            user_id (int): ID of the user to retrieve.
            current_user_id (int): ID of the authenticated user.

        Returns:
            UserModel: The found user.

        Raises:
            HTTPException: If attempting to access another user or the user does not exist.
        """
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied to access another user.",
            )

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user

    async def get_user_by_email(self, email: str) -> UserModel:
        """
        Returns a user by email address.

        Args:
            email (str): The user's email.

        Returns:
            UserModel: The found user.

        Raises:
            HTTPException: If no user is registered with this email.
        """
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with this email.",
            )

        return user

    async def forgot_password(self, email: str):
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return  # Silently ignore to prevent brute-force attacks

        reset_token = self.token_service.create_reset_token(sub=user.id)

        front_url = settings.FRONT_URL
        reset_link = f"{front_url}/login/change-password/{reset_token}"
        send_email(
            to=email,
            subject="Password Reset",
            body=f"Click the link to reset your password: {reset_link}",
        )

    async def reset_password_with_token(self, token: str, new_password: str):
        try:
            user_id = self.token_service.verify_reset_token(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        user.password = generator_hash_password(new_password)
        await self.db_session.commit()

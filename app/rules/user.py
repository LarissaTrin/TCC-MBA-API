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
                detail="Dados de acesso incorretos",
            )

        access_token = self.token_service.create_access_token(sub=user.id)

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        return TokenData(
            access_token=access_token,
            expires_at=expires_at,
        )

    async def create_user(self, user_data: UserSchemaCreate) -> UserModel:
        """
        Cria um novo usuário após verificar se o e-mail ou username já foram cadastrados.

        Args:
            user_data (UserSchemaCreate): Dados do novo usuário.

        Returns:
            UserModel: Usuário criado com sucesso.

        Raises:
            HTTPException: Se o e-mail ou username já existirem.
        """
        # Verifica e-mail
        email_query = select(UserModel).where(UserModel.email == user_data.email)
        result = await self.db_session.execute(email_query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já registrado.",
            )

        # Verifica username
        username_query = select(UserModel).where(
            UserModel.username == user_data.username
        )
        result = await self.db_session.execute(username_query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username já registrado.",
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
                detail="Erro ao criar usuário.",
            )

        except Exception:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro inesperado ao criar usuário.",
            )

    async def update_user(
        self, user_id: int, current_user_id: int, data: UserSchemaUp
    ) -> UserModel:
        """
        Atualiza os dados de um usuário, apenas se for o próprio usuário logado.

        Args:
            user_id (int): ID do usuário a ser editado.
            current_user_id (int): ID do usuário autenticado.
            data (UserSchemaUp): Dados a serem atualizados.

        Returns:
            UserModel: Usuário atualizado.

        Raises:
            HTTPException: Caso não seja o próprio usuário ou haja conflito de dados.
        """
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode editar sua própria conta.",
            )

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        # Verificar se novo e-mail já está em uso
        if data.email and data.email != user.email:
            email_query = select(UserModel).where(UserModel.email == data.email)
            result = await self.db_session.execute(email_query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="E-mail já está em uso por outro usuário.",
                )

        # Atualizar campos
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
                detail="Erro ao atualizar o usuário.",
            )
        except Exception:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Erro inesperado ao atualizar o usuário.",
            )

    async def get_user_by_id(self, user_id: int, current_user_id: int) -> UserModel:
        """
        Busca um usuário pelo ID, mas só permite acessar se for o próprio usuário logado.

        Args:
            user_id (int): ID do usuário que se quer buscar.
            current_user_id (int): ID do usuário autenticado (logado).

        Returns:
            UserModel: Usuário encontrado.

        Raises:
            HTTPException: Se tentar acessar usuário diferente do logado ou usuário não existir.
        """
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada para acessar outro usuário.",
            )

        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        return user

    async def get_user_by_email(self, email: str) -> UserModel:
        """
        Retorna um usuário pelo e-mail.

        Args:
            email (str): E-mail do usuário.

        Returns:
            UserModel: Usuário encontrado.

        Raises:
            HTTPException: Se o e-mail não estiver registrado.
        """
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado com este e-mail.",
            )

        return user

    async def forgot_password(self, email: str):
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return  # Silenciosamente ignora para evitar brute-force

        access_token = self.token_service.create_access_token(sub=user.id, minutes=60)

        reset_link = f"https://seusite.com/reset-password?token={access_token}"
        send_email(
            to=email,
            subject="Redefinição de senha",
            body=f"Clique no link para redefinir sua senha: {reset_link}",
        )

    async def reset_password(self, user_id: int, new_password: str):
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        user.password = generator_hash_password(new_password)
        await self.db_session.commit()

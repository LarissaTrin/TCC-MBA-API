from pytz import timezone

from typing import Optional
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from jose import jwt

from pydantic import EmailStr

from app.db.models.user_model import UserModel
from app.core.configs import settings
from app.core.security import verification_password

oaut2_schema = OAuth2PasswordBearer(tokenUrl=f"{settings.API_STR}/users/login")


class TokenService:
    SECRET_KEY = settings.JWT_SECRET
    ALGORITHM = settings.ALGORITHM
    VERIFICATION_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    async def authenticate(
        self, email: EmailStr, password: str, db: AsyncSession
    ) -> Optional[UserModel]:
        async with db as session:
            query = select(UserModel).filter(UserModel.email == email)
            result = await session.execute(query)

            user: UserModel = result.scalars().unique().one_or_none()

            if not user:
                return None
            if not verification_password(password, user.password):
                return None

            return user

    def _create_token(self, type_token: str, life_temp: timedelta, sub: str) -> str:
        # https://datatracker.ietf.org/doc/html/rfc7519#saction-4.1.3
        payload = {}
        sp = timezone("America/Sao_Paulo")
        date_now = datetime.now(tz=sp)

        payload["type"] = type_token

        payload["exp"] = date_now + life_temp

        payload["iat"] = date_now

        payload["sub"] = str(sub)

        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_access_token(self, sub: str, minutes: int | None = None) -> str:
        """Cria um token de acesso com tempo de vida variável."""
        token_lifetime = timedelta(
            minutes=minutes or self.VERIFICATION_TOKEN_EXPIRE_MINUTES
        )

        return self._create_token(
            type_token="access_token",
            life_temp=token_lifetime,
            sub=sub,
        )

    def verify_verification_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("type") != "verification":
                raise ValueError("Tipo de token inválido.")
            return int(payload.get("sub"))
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado.")
        except jwt.JWTError:
            raise ValueError("Token inválido.")

"""Tests for app/core/auth.py — TokenService."""
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from core.auth import TokenService
from core.configs import settings
from jose import jwt


@pytest.fixture
def service():
    return TokenService()


# ── create_access_token ───────────────────────────────────────────────────────

def test_create_access_token_returns_string(service):
    token = service.create_access_token(sub="42")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_payload(service):
    token = service.create_access_token(sub="99")
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.ALGORITHM],
        options={"verify_aud": False},
    )
    assert payload["sub"] == "99"
    assert payload["type"] == "access_token"


def test_create_access_token_custom_minutes(service):
    token = service.create_access_token(sub="1", minutes=1)
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.ALGORITHM],
        options={"verify_aud": False},
    )
    assert payload["sub"] == "1"


# ── create_reset_token ────────────────────────────────────────────────────────

def test_create_reset_token_returns_string(service):
    token = service.create_reset_token(sub="7")
    assert isinstance(token, str)


def test_create_reset_token_type(service):
    token = service.create_reset_token(sub="7")
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.ALGORITHM],
        options={"verify_aud": False},
    )
    assert payload["type"] == "password_reset"
    assert payload["sub"] == "7"


# ── verify_reset_token ────────────────────────────────────────────────────────

def test_verify_reset_token_valid(service):
    token = service.create_reset_token(sub="5")
    user_id = service.verify_reset_token(token)
    assert user_id == 5


def test_verify_reset_token_wrong_type_raises(service):
    token = service.create_access_token(sub="5")
    with pytest.raises(ValueError, match="TOKEN_INVALID"):
        service.verify_reset_token(token)


def test_verify_reset_token_garbage_raises(service):
    with pytest.raises(ValueError, match="TOKEN_INVALID"):
        service.verify_reset_token("not.a.valid.token")


def test_verify_reset_token_expired_raises(service):
    # Create a token that expired in the past
    expired = service._create_token(
        type_token="password_reset",
        life_temp=timedelta(seconds=-1),
        sub="3",
    )
    with pytest.raises(ValueError, match="TOKEN_EXPIRED"):
        service.verify_reset_token(expired)


# ── authenticate ──────────────────────────────────────────────────────────────

async def test_authenticate_user_not_found_returns_none(service):
    mock_session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    mock_db = MagicMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    user = await service.authenticate("unknown@test.com", "pass", mock_db)
    assert user is None


async def test_authenticate_wrong_password_returns_none(service):
    from core.security import generator_hash_password

    mock_user = MagicMock()
    mock_user.password = generator_hash_password("correct")

    mock_session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=result)

    mock_db = MagicMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    user = await service.authenticate("user@test.com", "wrong", mock_db)
    assert user is None


async def test_authenticate_success(service):
    from core.security import generator_hash_password

    mock_user = MagicMock()
    mock_user.password = generator_hash_password("correct")

    mock_session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=result)

    mock_db = MagicMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    user = await service.authenticate("user@test.com", "correct", mock_db)
    assert user is mock_user

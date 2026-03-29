"""Tests for app/rules/user.py — UserRules."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from rules.user import UserRules
from schemas.user_schema import UserSchemaCreate, UserSchemaUp
from app.test.rules.conftest import make_session, make_result


def _make_user(user_id=1, email="test@test.com", username="testuser",
               first_name="Test", last_name="User"):
    u = MagicMock()
    u.id = user_id
    u.email = email
    u.username = username
    u.firstName = first_name
    u.lastName = last_name
    u.password = "hashed"
    u.isAdmin = False
    return u


# ── _generate_username ────────────────────────────────────────────────────────

def test_generate_username_basic():
    session = make_session()
    rules = UserRules(session)
    username = rules._generate_username("John", "Doe")
    assert username.startswith("johndoe")
    assert len(username) > len("johndoe")


def test_generate_username_removes_special_chars():
    session = make_session()
    rules = UserRules(session)
    username = rules._generate_username("José", "D'Silva")
    assert username.startswith("josdsilva") or "jos" in username


def test_generate_username_empty_names():
    session = make_session()
    rules = UserRules(session)
    username = rules._generate_username("", "")
    assert username.startswith("user")


# ── login ─────────────────────────────────────────────────────────────────────

async def test_login_invalid_credentials_raises():
    session = make_session()
    rules = UserRules(session)
    rules.token_service.authenticate = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await rules.login("bad@email.com", "wrong")
    assert exc.value.status_code == 400


async def test_login_success_returns_token_data():
    session = make_session()
    rules = UserRules(session)

    user = _make_user(user_id=5, first_name="Alice", last_name="Wonder")
    rules.token_service.authenticate = AsyncMock(return_value=user)
    rules.token_service.create_access_token = MagicMock(return_value="mock.jwt.token")

    result = await rules.login("alice@test.com", "correct")

    assert result.access_token == "mock.jwt.token"
    assert result.user_id == 5


# ── create_user ───────────────────────────────────────────────────────────────

async def test_create_user_email_taken_raises():
    session = make_session()
    existing = _make_user(email="taken@test.com")
    session.execute.return_value = make_result(scalar=existing)

    rules = UserRules(session)
    data = UserSchemaCreate(
        first_name="A", last_name="B", email="taken@test.com", password="pass123"
    )
    with pytest.raises(HTTPException) as exc:
        await rules.create_user(data)
    assert exc.value.status_code == 409
    assert "Email" in exc.value.detail


async def test_create_user_username_taken_raises():
    session = make_session()
    # first call (email check) → None; second call (username check) → existing user
    none_result = make_result(scalar=None)
    taken_result = make_result(scalar=_make_user())
    session.execute = AsyncMock(side_effect=[none_result, taken_result])

    rules = UserRules(session)
    data = UserSchemaCreate(
        first_name="A", last_name="B", email="new@test.com",
        password="pass123", username="taken"
    )
    with pytest.raises(HTTPException) as exc:
        await rules.create_user(data)
    assert exc.value.status_code == 409
    assert "Username" in exc.value.detail


async def test_create_user_with_username_success():
    session = make_session()
    none_result = make_result(scalar=None)
    session.execute = AsyncMock(return_value=none_result)

    new_user = _make_user()
    session.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", 1))

    rules = UserRules(session)
    data = UserSchemaCreate(
        first_name="A", last_name="B", email="new@test.com",
        password="pass123", username="myuser"
    )
    result = await rules.create_user(data)

    session.add.assert_called_once()
    session.commit.assert_called()


async def test_create_user_auto_username():
    session = make_session()
    none_result = make_result(scalar=None)
    session.execute = AsyncMock(return_value=none_result)

    rules = UserRules(session)
    data = UserSchemaCreate(
        first_name="John", last_name="Doe",
        email="john@test.com", password="pass123"
    )
    await rules.create_user(data)
    session.add.assert_called_once()


async def test_create_user_integrity_error_raises():
    session = make_session()
    none_result = make_result(scalar=None)
    session.execute = AsyncMock(return_value=none_result)
    session.commit = AsyncMock(side_effect=IntegrityError("", {}, None))

    rules = UserRules(session)
    data = UserSchemaCreate(
        first_name="A", last_name="B", email="e@test.com",
        password="pass", username="u"
    )
    with pytest.raises(HTTPException) as exc:
        await rules.create_user(data)
    assert exc.value.status_code == 400
    session.rollback.assert_called_once()


async def test_create_user_unexpected_exception_raises():
    session = make_session()
    none_result = make_result(scalar=None)
    session.execute = AsyncMock(return_value=none_result)
    session.commit = AsyncMock(side_effect=RuntimeError("boom"))

    rules = UserRules(session)
    data = UserSchemaCreate(
        first_name="A", last_name="B", email="e@test.com",
        password="pass", username="u"
    )
    with pytest.raises(HTTPException) as exc:
        await rules.create_user(data)
    assert exc.value.status_code == 500
    session.rollback.assert_called_once()


# ── update_user ───────────────────────────────────────────────────────────────

async def test_update_user_different_user_raises():
    session = make_session()
    rules = UserRules(session)
    data = UserSchemaUp()

    with pytest.raises(HTTPException) as exc:
        await rules.update_user(user_id=1, current_user_id=2, data=data)
    assert exc.value.status_code == 403


async def test_update_user_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = UserRules(session)
    data = UserSchemaUp()

    with pytest.raises(HTTPException) as exc:
        await rules.update_user(user_id=1, current_user_id=1, data=data)
    assert exc.value.status_code == 404


async def test_update_user_email_taken_raises():
    session = make_session()
    user = _make_user(email="old@test.com")
    other = _make_user(user_id=2, email="taken@test.com")

    session.execute = AsyncMock(side_effect=[
        make_result(scalar=user),
        make_result(scalar=other),
    ])

    rules = UserRules(session)
    data = UserSchemaUp(email="taken@test.com")

    with pytest.raises(HTTPException) as exc:
        await rules.update_user(user_id=1, current_user_id=1, data=data)
    assert exc.value.status_code == 409


async def test_update_user_success():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)

    rules = UserRules(session)
    data = UserSchemaUp(first_name="NewName")
    result = await rules.update_user(user_id=1, current_user_id=1, data=data)

    assert user.firstName == "NewName"
    session.commit.assert_called_once()


async def test_update_user_integrity_error_raises():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)
    session.commit = AsyncMock(side_effect=IntegrityError("", {}, None))

    rules = UserRules(session)
    data = UserSchemaUp(first_name="X")
    with pytest.raises(HTTPException) as exc:
        await rules.update_user(user_id=1, current_user_id=1, data=data)
    assert exc.value.status_code == 400


async def test_update_user_unexpected_exception_raises():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)
    session.commit = AsyncMock(side_effect=RuntimeError("boom"))

    rules = UserRules(session)
    data = UserSchemaUp(first_name="X")
    with pytest.raises(HTTPException) as exc:
        await rules.update_user(user_id=1, current_user_id=1, data=data)
    assert exc.value.status_code == 500


# ── get_user_by_id ────────────────────────────────────────────────────────────

async def test_get_user_by_id_different_user_raises():
    session = make_session()
    rules = UserRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.get_user_by_id(user_id=1, current_user_id=2)
    assert exc.value.status_code == 403


async def test_get_user_by_id_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = UserRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.get_user_by_id(user_id=1, current_user_id=1)
    assert exc.value.status_code == 404


async def test_get_user_by_id_success():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)
    rules = UserRules(session)

    result = await rules.get_user_by_id(user_id=1, current_user_id=1)
    assert result is user


# ── get_user_by_email ─────────────────────────────────────────────────────────

async def test_get_user_by_email_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = UserRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.get_user_by_email("missing@test.com")
    assert exc.value.status_code == 404


async def test_get_user_by_email_success():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)
    rules = UserRules(session)

    result = await rules.get_user_by_email("test@test.com")
    assert result is user


# ── forgot_password ───────────────────────────────────────────────────────────

async def test_forgot_password_user_not_found_returns_silently():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = UserRules(session)

    # Should not raise, just return silently
    await rules.forgot_password("ghost@test.com")


async def test_forgot_password_sends_email():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)

    rules = UserRules(session)
    rules.token_service.create_reset_token = MagicMock(return_value="resettoken")

    with patch("rules.user.send_email") as mock_email:
        await rules.forgot_password("test@test.com")
    mock_email.assert_called_once()


# ── reset_password_with_token ─────────────────────────────────────────────────

async def test_reset_password_invalid_token_raises():
    session = make_session()
    rules = UserRules(session)
    rules.token_service.verify_reset_token = MagicMock(
        side_effect=ValueError("TOKEN_INVALID")
    )

    with pytest.raises(HTTPException) as exc:
        await rules.reset_password_with_token("badtoken", "newpass")
    assert exc.value.status_code == 400


async def test_reset_password_user_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = UserRules(session)
    rules.token_service.verify_reset_token = MagicMock(return_value=99)

    with pytest.raises(HTTPException) as exc:
        await rules.reset_password_with_token("validtoken", "newpass")
    assert exc.value.status_code == 404


async def test_reset_password_success():
    session = make_session()
    user = _make_user()
    session.execute.return_value = make_result(scalar=user)

    rules = UserRules(session)
    rules.token_service.verify_reset_token = MagicMock(return_value=1)

    await rules.reset_password_with_token("validtoken", "newpassword")

    assert user.password != "hashed"
    session.commit.assert_called_once()

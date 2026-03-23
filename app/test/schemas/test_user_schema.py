import pytest
from datetime import datetime

from schemas.user_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenData,
    UserSchemaBase,
    UserSchemaCreate,
    UserSchemaUp,
)


# ── UserSchemaCreate ──────────────────────────────────────────────────────────


def test_user_schema():
    user = UserSchemaCreate(
        username="Larissa",
        password="pass#",
        first_name="Larissa",
        last_name="Trindade",
        email="email@mail.com",
    )
    result = user.dict()
    assert result["username"] == "Larissa"
    assert result["password"] == "pass#"
    assert result["first_name"] == "Larissa"
    assert result["last_name"] == "Trindade"
    assert result["email"] == "email@mail.com"
    assert result["is_admin"] is False


def test_user_schema_without_username():
    """Username is auto-generated when not provided."""
    user = UserSchemaCreate(
        password="pass#",
        first_name="Larissa",
        last_name="Trindade",
        email="email@mail.com",
    )
    result = user.dict()
    assert result.get("username") is None
    assert result["first_name"] == "Larissa"


def test_user_schema_invalid_username():
    with pytest.raises(ValueError):
        UserSchemaCreate(
            username="InvalidUser#%&!ã",
            password="pass#",
            first_name="Larissa",
            last_name="Trindade",
            email="email@mail.com",
        )

    with pytest.raises(ValueError):
        UserSchemaCreate(
            username="Larissa",
            password="pass#",
            first_name="Larissa",
            last_name="Trindade",
            email="invalid_email",
        )


def test_user_schema_valid_username_with_special_chars():
    user = UserSchemaCreate(
        username="user_01-test@",
        password="pass",
        first_name="Test",
        last_name="User",
        email="test@mail.com",
    )
    assert user.username == "user_01-test@"


# ── UserSchemaBase ────────────────────────────────────────────────────────────


def test_user_schema_base_is_admin_defaults_false():
    user = UserSchemaBase(
        username="admin01",
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
    )
    assert user.is_admin is False


def test_user_schema_base_is_admin_true():
    user = UserSchemaBase(
        username="admin01",
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        is_admin=True,
    )
    assert user.dict()["is_admin"] is True


def test_user_schema_base_optional_id_absent():
    user = UserSchemaBase(
        username="u1",
        first_name="X",
        last_name="Y",
        email="x@mail.com",
    )
    # id is None → filtered by CustomBaseModel.dict()
    assert "id" not in user.dict()


def test_user_schema_base_with_id():
    user = UserSchemaBase(
        id=42,
        username="u1",
        first_name="X",
        last_name="Y",
        email="x@mail.com",
    )
    assert user.dict()["id"] == 42


# ── UserSchemaUp ──────────────────────────────────────────────────────────────


def test_user_schema_up_all_optional():
    # All fields are now optional — can construct with no fields
    schema = UserSchemaUp()
    result = schema.dict()
    # All None values are filtered by CustomBaseModel.dict()
    assert result == {}


def test_user_schema_up_with_username():
    schema = UserSchemaUp(username="u", first_name="F", last_name="L", email="f@mail.com")
    result = schema.dict()
    assert result["username"] == "u"


def test_user_schema_up_partial_update():
    schema = UserSchemaUp(
        username="u",
        first_name="NewFirst",
        last_name="L",
        email="f@mail.com",
        password="newpass",
    )
    result = schema.dict()
    assert result["first_name"] == "NewFirst"
    assert result["password"] == "newpass"


# ── TokenData ─────────────────────────────────────────────────────────────────


def test_token_date_schema():
    expires_at = datetime.now()
    token_data = TokenData(access_token="any token", expires_at=expires_at)
    assert token_data.dict() == {"access_token": "any token", "expires_at": expires_at}


def test_token_data_optional_fields_absent():
    token = TokenData(access_token="tok", expires_at=datetime.now())
    result = token.dict()
    assert "user_id" not in result
    assert "first_name" not in result
    assert "last_name" not in result


def test_token_data_with_all_fields():
    expires_at = datetime.now()
    token = TokenData(
        access_token="tok",
        expires_at=expires_at,
        user_id=1,
        first_name="Ana",
        last_name="Costa",
    )
    result = token.dict()
    assert result["user_id"] == 1
    assert result["first_name"] == "Ana"
    assert result["last_name"] == "Costa"


# ── ForgotPasswordRequest ─────────────────────────────────────────────────────


def test_forgot_password_request_valid():
    req = ForgotPasswordRequest(email="user@example.com")
    assert req.dict()["email"] == "user@example.com"


def test_forgot_password_request_invalid_email():
    with pytest.raises(ValueError):
        ForgotPasswordRequest(email="not-an-email")


# ── ResetPasswordRequest ──────────────────────────────────────────────────────


def test_reset_password_request():
    req = ResetPasswordRequest(new_password="secure123")
    assert req.dict() == {"new_password": "secure123"}

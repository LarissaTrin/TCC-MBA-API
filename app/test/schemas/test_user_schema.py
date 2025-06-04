import pytest
from datetime import datetime

from schemas.user_schema import TokenData, UserSchemaCreate


def test_user_schema():
    user = UserSchemaCreate(
        username="Larissa",
        password="pass#",
        first_name="Larissa",
        last_name="Trindade",
        email="email@mail.com",
    )

    assert user.dict() == {
        "username": "Larissa",
        "password": "pass#",
        "first_name": "Larissa",
        "last_name": "Trindade",
        "email": "email@mail.com",
    }


def test_user_schema_invalid_username():
    with pytest.raises(ValueError):
        user = UserSchemaCreate(
            username="InvalidUser#%&!ã",
            password="pass#",
            first_name="Larissa",
            last_name="Trindade",
            email="email@mail.com",
        )

    with pytest.raises(ValueError):
        user = UserSchemaCreate(
            username="Larissa",
            password="pass#",
            first_name="Larissa",
            last_name="Trindade",
            email="invalid_email",
        )


def test_token_date_schema():
    expires_at = datetime.now()
    token_data = TokenData(access_token="any token", expires_at=expires_at)

    assert token_data.dict() == {"access_token": "any token", "expires_at": expires_at}

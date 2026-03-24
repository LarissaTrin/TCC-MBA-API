import pytest

from schemas.role_schema import RoleSchemaBase


# ── RoleSchemaBase ────────────────────────────────────────────────────────────


def test_role_schema_base_required_fields():
    schema = RoleSchemaBase(id=1, name="Admin")
    result = schema.dict()
    assert result["id"] == 1
    assert result["name"] == "Admin"


def test_role_schema_base_user_role():
    schema = RoleSchemaBase(id=2, name="User")
    assert schema.dict()["name"] == "User"


def test_role_schema_base_missing_id():
    with pytest.raises(Exception):
        RoleSchemaBase(name="Leader")


def test_role_schema_base_missing_name():
    with pytest.raises(Exception):
        RoleSchemaBase(id=3)

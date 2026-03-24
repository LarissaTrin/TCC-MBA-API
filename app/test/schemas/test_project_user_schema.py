import pytest

from schemas.project_user_schema import (
    ProjectMemberSearchItem,
    ProjectUserSchema,
    ProjectUserSchemaBase,
    UpdateMemberRoleRequest,
)


# ── ProjectUserSchemaBase ─────────────────────────────────────────────────────


def test_project_user_schema_base_required_fields():
    schema = ProjectUserSchemaBase(user_id=1, role_id=2)
    result = schema.dict()
    assert result["user_id"] == 1
    assert result["role_id"] == 2
    assert "id" not in result


def test_project_user_schema_base_with_id():
    schema = ProjectUserSchemaBase(id=10, user_id=5, role_id=3)
    result = schema.dict()
    assert result["id"] == 10
    assert result["user_id"] == 5
    assert result["role_id"] == 3


def test_project_user_schema_base_missing_user_id():
    with pytest.raises(Exception):
        ProjectUserSchemaBase(role_id=2)


def test_project_user_schema_base_missing_role_id():
    with pytest.raises(Exception):
        ProjectUserSchemaBase(user_id=1)


# ── ProjectUserSchema ─────────────────────────────────────────────────────────


def test_project_user_schema_no_nested():
    schema = ProjectUserSchema(user_id=2, role_id=1)
    result = schema.dict()
    assert result["user_id"] == 2
    assert result["role_id"] == 1
    assert "user" not in result
    assert "role" not in result


def test_project_user_schema_with_user_and_role():
    from schemas.user_schema import UserSchemaBase
    from schemas.role_schema import RoleSchemaBase

    user = UserSchemaBase(
        id=3,
        username="bob",
        first_name="Bob",
        last_name="Jones",
        email="bob@mail.com",
    )
    role = RoleSchemaBase(id=1, name="Admin")
    schema = ProjectUserSchema(user_id=3, role_id=1, user=user, role=role)
    result = schema.dict()
    assert result["user"]["username"] == "bob"
    assert result["role"]["name"] == "Admin"


# ── ProjectMemberSearchItem ───────────────────────────────────────────────────


def test_project_member_search_item():
    schema = ProjectMemberSearchItem(
        id=7, first_name="Carlos", last_name="Lima", email="carlos@mail.com"
    )
    result = schema.dict()
    assert result["id"] == 7
    assert result["first_name"] == "Carlos"
    assert result["last_name"] == "Lima"
    assert result["email"] == "carlos@mail.com"


def test_project_member_search_item_invalid_email():
    with pytest.raises(Exception):
        ProjectMemberSearchItem(
            id=1, first_name="X", last_name="Y", email="not-an-email"
        )


# ── UpdateMemberRoleRequest ───────────────────────────────────────────────────


def test_update_member_role_request():
    schema = UpdateMemberRoleRequest(role="Leader")
    assert schema.dict()["role"] == "Leader"


def test_update_member_role_request_missing():
    with pytest.raises(Exception):
        UpdateMemberRoleRequest()

import pytest

from schemas.project_schema import (
    InviteEntry,
    InviteUserResult,
    InviteUsersRequest,
    InviteUsersResponse,
    ProjectSchemaBase,
    ProjectSchemaUp,
)


# ── ProjectSchemaBase ─────────────────────────────────────────────────────────


def test_project_schema_create():
    project = ProjectSchemaBase(title="Project 1", description="Description project 1")

    assert project.dict() == {
        "title": "Project 1",
        "description": "Description project 1",
    }


def test_project_schema_base_missing_title():
    with pytest.raises(Exception):
        ProjectSchemaBase(description="desc")


def test_project_schema_base_missing_description():
    with pytest.raises(Exception):
        ProjectSchemaBase(title="My Project")


# ── ProjectSchemaUp ───────────────────────────────────────────────────────────


def test_project_schema_up_all_none():
    schema = ProjectSchemaUp()
    result = schema.dict()
    assert result == {}


def test_project_schema_up_title_only():
    schema = ProjectSchemaUp(title="Renamed")
    result = schema.dict()
    assert result["title"] == "Renamed"
    assert "description" not in result
    assert "lists" not in result


def test_project_schema_up_with_description():
    schema = ProjectSchemaUp(description="New description")
    result = schema.dict()
    assert result["description"] == "New description"
    assert "title" not in result


# ── InviteEntry ───────────────────────────────────────────────────────────────


def test_invite_entry_default_role():
    entry = InviteEntry(email="user@mail.com")
    result = entry.dict()
    assert result["email"] == "user@mail.com"
    assert result["role"] == "User"


def test_invite_entry_custom_role():
    entry = InviteEntry(email="lead@mail.com", role="Leader")
    assert entry.dict()["role"] == "Leader"


def test_invite_entry_missing_email():
    with pytest.raises(Exception):
        InviteEntry()


# ── InviteUsersRequest ────────────────────────────────────────────────────────


def test_invite_users_request_single():
    req = InviteUsersRequest(invites=[InviteEntry(email="a@mail.com")])
    result = req.dict()
    assert len(result["invites"]) == 1
    assert result["invites"][0]["email"] == "a@mail.com"


def test_invite_users_request_empty():
    req = InviteUsersRequest(invites=[])
    assert req.dict() == {"invites": []}


def test_invite_users_request_multiple():
    req = InviteUsersRequest(
        invites=[
            InviteEntry(email="a@mail.com", role="Admin"),
            InviteEntry(email="b@mail.com"),
        ]
    )
    result = req.dict()
    assert len(result["invites"]) == 2
    assert result["invites"][0]["role"] == "Admin"
    assert result["invites"][1]["role"] == "User"


# ── InviteUserResult ──────────────────────────────────────────────────────────


def test_invite_user_result_registered():
    result = InviteUserResult(email="x@mail.com", registered=True)
    d = result.dict()
    assert d["email"] == "x@mail.com"
    assert d["registered"] is True
    assert d["already_member"] is False


def test_invite_user_result_already_member():
    result = InviteUserResult(email="x@mail.com", registered=True, already_member=True)
    assert result.dict()["already_member"] is True


def test_invite_user_result_not_registered():
    result = InviteUserResult(email="new@mail.com", registered=False)
    assert result.dict()["registered"] is False


# ── InviteUsersResponse ───────────────────────────────────────────────────────


def test_invite_users_response_empty():
    schema = InviteUsersResponse(results=[])
    assert schema.dict() == {"results": []}


def test_invite_users_response_with_results():
    results = [
        InviteUserResult(email="a@mail.com", registered=True),
        InviteUserResult(email="b@mail.com", registered=False),
    ]
    schema = InviteUsersResponse(results=results)
    d = schema.dict()
    assert len(d["results"]) == 2
    assert d["results"][0]["registered"] is True
    assert d["results"][1]["registered"] is False

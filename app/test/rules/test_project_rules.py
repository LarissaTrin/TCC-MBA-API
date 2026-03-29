"""Tests for app/rules/project.py — ProjectRules."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

from rules.project import ProjectRules
from schemas.project_schema import ProjectSchemaBase, ProjectSchemaUp
from schemas.project_user_schema import ProjectUserSchemaBase
from app.test.rules.conftest import make_session, make_result


def _make_project(project_id=1, title="My Project", creator_id=1):
    p = MagicMock()
    p.id = project_id
    p.title = title
    p.creator_id = creator_id
    p.lists = []
    p.project_users = []
    return p


def _make_project_user(pu_id=1, user_id=1, role_id=1):
    pu = MagicMock()
    pu.id = pu_id
    pu.user_id = user_id
    pu.role_id = role_id
    return pu


def _make_user(user_id=1, email="user@test.com"):
    u = MagicMock()
    u.id = user_id
    u.email = email
    return u


# ── add_project ───────────────────────────────────────────────────────────────

async def test_add_project_success():
    session = make_session()
    role_id_result = make_result(scalar=2)
    session.execute.return_value = role_id_result

    rules = ProjectRules(session)
    data = ProjectSchemaBase(title="New Project", description="desc")
    await rules.add_project(data, creator_id=1)

    session.add.assert_called()
    session.commit.assert_called()


async def test_add_project_no_super_admin_role_raises():
    session = make_session()
    # first commit succeeds, execute (role query) returns None
    session.execute.return_value = make_result(scalar=None)

    rules = ProjectRules(session)
    data = ProjectSchemaBase(title="X", description="d")
    with pytest.raises(Exception):
        await rules.add_project(data, creator_id=1)


async def test_add_project_db_exception_rollbacks():
    session = make_session()
    session.commit = AsyncMock(side_effect=RuntimeError("db error"))

    rules = ProjectRules(session)
    data = ProjectSchemaBase(title="X", description="d")
    with pytest.raises(RuntimeError):
        await rules.add_project(data, creator_id=1)
    session.rollback.assert_called_once()


# ── get_project_by_id_and_user ────────────────────────────────────────────────

async def test_get_project_by_id_and_user_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = ProjectRules(session)
    with pytest.raises(NoResultFound):
        await rules.get_project_by_id_and_user(project_id=99, user_id=1)


async def test_get_project_by_id_and_user_success():
    session = make_session()
    project = _make_project()
    session.execute.return_value = make_result(scalar=project)

    rules = ProjectRules(session)
    result = await rules.get_project_by_id_and_user(project_id=1, user_id=1)
    assert result is project


# ── get_projects_for_user ─────────────────────────────────────────────────────

async def test_get_projects_for_user_returns_list():
    session = make_session()
    projects = [_make_project(1), _make_project(2)]
    session.execute.return_value = make_result(scalars_list=projects)

    rules = ProjectRules(session)
    result = await rules.get_projects_for_user(user_id=1)
    assert result == projects


# ── update_project ────────────────────────────────────────────────────────────

async def test_update_project_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")

    rules = ProjectRules(session)
    data = ProjectSchemaUp(title="X")
    with pytest.raises(HTTPException) as exc:
        await rules.update_project(project_id=1, data=data, user_id=99)
    assert exc.value.status_code == 403


async def test_update_project_not_found_raises():
    session = make_session()
    perm_result = make_result(scalar="Admin")
    not_found = make_result(scalar=None)
    session.execute = AsyncMock(side_effect=[perm_result, not_found])

    rules = ProjectRules(session)
    data = ProjectSchemaUp(title="X")
    with pytest.raises(HTTPException) as exc:
        await rules.update_project(project_id=99, data=data, user_id=1)
    assert exc.value.status_code == 404


async def test_update_project_success():
    session = make_session()
    project = _make_project()
    perm_result = make_result(scalar="Admin")
    project_result = make_result(scalar=project)
    session.execute = AsyncMock(side_effect=[perm_result, project_result])

    rules = ProjectRules(session)
    data = ProjectSchemaUp(title="Renamed")
    result = await rules.update_project(project_id=1, data=data, user_id=1)

    assert project.title == "Renamed"
    session.commit.assert_called_once()


# ── delete_project ────────────────────────────────────────────────────────────

async def test_delete_project_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = ProjectRules(session)
    with pytest.raises(Exception, match="not found"):
        await rules.delete_project(project_id=99, user_id=1)


async def test_delete_project_not_creator_raises():
    session = make_session()
    project = _make_project(creator_id=5)
    session.execute.return_value = make_result(scalar=project)

    rules = ProjectRules(session)
    with pytest.raises(Exception, match="not authorized"):
        await rules.delete_project(project_id=1, user_id=99)


async def test_delete_project_success():
    session = make_session()
    project = _make_project(creator_id=1)
    session.execute.return_value = make_result(scalar=project)

    rules = ProjectRules(session)
    await rules.delete_project(project_id=1, user_id=1)

    session.delete.assert_called_once_with(project)
    session.commit.assert_called_once()


# ── update_project_users ──────────────────────────────────────────────────────

async def test_update_project_users_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")

    rules = ProjectRules(session)
    with pytest.raises(PermissionError):
        await rules.update_project_users(project_id=1, users_data=[], current_user_id=99)


async def test_update_project_users_project_not_found_raises():
    session = make_session()
    perm_result = make_result(scalar="Admin")
    not_found = make_result(scalar=None)
    session.execute = AsyncMock(side_effect=[perm_result, not_found])

    rules = ProjectRules(session)
    with pytest.raises(Exception, match="not found"):
        await rules.update_project_users(project_id=99, users_data=[], current_user_id=1)


async def test_update_project_users_success_adds_new():
    session = make_session()
    project = _make_project()
    project.project_users = []

    perm_result = make_result(scalar="SuperAdmin")
    project_result = make_result(scalar=project)
    session.execute = AsyncMock(side_effect=[perm_result, project_result])

    rules = ProjectRules(session)
    new_user = ProjectUserSchemaBase(user_id=5, role_id=2)
    await rules.update_project_users(project_id=1, users_data=[new_user], current_user_id=1)

    session.add.assert_called_once()
    session.commit.assert_called_once()


# ── search_project_members ────────────────────────────────────────────────────

async def test_search_project_members_not_member_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = ProjectRules(session)
    with pytest.raises(HTTPException) as exc:
        await rules.search_project_members(project_id=1, current_user_id=99, query="John")
    assert exc.value.status_code == 403


async def test_search_project_members_success():
    session = make_session()
    member_check = make_result(scalar=1)
    users = [_make_user(1), _make_user(2)]
    users_result = MagicMock()
    users_result.scalars.return_value.all.return_value = users

    session.execute = AsyncMock(side_effect=[member_check, users_result])
    rules = ProjectRules(session)

    result = await rules.search_project_members(project_id=1, current_user_id=1, query="Jo")
    assert result == users


# ── remove_project_member ─────────────────────────────────────────────────────

async def test_remove_member_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = ProjectRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.remove_project_member(project_id=1, user_id_to_remove=2, current_user_id=99)
    assert exc.value.status_code == 403


async def test_remove_member_cannot_remove_super_admin():
    session = make_session()
    caller_role = make_result(scalar="Admin")
    target_role = make_result(scalar="SuperAdmin")
    session.execute = AsyncMock(side_effect=[caller_role, target_role])

    rules = ProjectRules(session)
    with pytest.raises(HTTPException) as exc:
        await rules.remove_project_member(project_id=1, user_id_to_remove=5, current_user_id=1)
    assert exc.value.status_code == 400


async def test_remove_member_not_found_raises():
    session = make_session()
    caller_role = make_result(scalar="Admin")
    target_role = make_result(scalar="User")
    not_found = make_result(scalar=None)
    session.execute = AsyncMock(side_effect=[caller_role, target_role, not_found])

    rules = ProjectRules(session)
    with pytest.raises(HTTPException) as exc:
        await rules.remove_project_member(project_id=1, user_id_to_remove=5, current_user_id=1)
    assert exc.value.status_code == 404


async def test_remove_member_success():
    session = make_session()
    member = _make_project_user()
    caller_role = make_result(scalar="Admin")
    target_role = make_result(scalar="User")
    member_result = make_result(scalar=member)
    session.execute = AsyncMock(side_effect=[caller_role, target_role, member_result])

    rules = ProjectRules(session)
    await rules.remove_project_member(project_id=1, user_id_to_remove=2, current_user_id=1)

    session.delete.assert_called_once_with(member)
    session.commit.assert_called_once()


# ── update_member_role ────────────────────────────────────────────────────────

async def test_update_member_role_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = ProjectRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.update_member_role(
            project_id=1, target_user_id=2, new_role="Admin", current_user_id=99
        )
    assert exc.value.status_code == 403


async def test_update_member_role_cannot_change_super_admin():
    session = make_session()
    caller = make_result(scalar="Admin")
    target = make_result(scalar="SuperAdmin")
    session.execute = AsyncMock(side_effect=[caller, target])

    rules = ProjectRules(session)
    with pytest.raises(HTTPException) as exc:
        await rules.update_member_role(
            project_id=1, target_user_id=5, new_role="User", current_user_id=1
        )
    assert exc.value.status_code == 400


async def test_update_member_role_invalid_role_for_admin():
    session = make_session()
    caller = make_result(scalar="Admin")
    target = make_result(scalar="User")
    session.execute = AsyncMock(side_effect=[caller, target])

    rules = ProjectRules(session)
    with pytest.raises(HTTPException) as exc:
        await rules.update_member_role(
            project_id=1, target_user_id=2, new_role="Admin", current_user_id=1
        )
    assert exc.value.status_code == 400


async def test_update_member_role_success():
    session = make_session()
    role_obj = MagicMock()
    role_obj.id = 3
    member = _make_project_user()

    caller = make_result(scalar="SuperAdmin")
    target = make_result(scalar="User")
    role_result = make_result(scalar=role_obj)
    member_result = make_result(scalar=member)

    session.execute = AsyncMock(side_effect=[caller, target, role_result, member_result])
    rules = ProjectRules(session)

    await rules.update_member_role(
        project_id=1, target_user_id=2, new_role="Leader", current_user_id=1
    )
    assert member.role_id == role_obj.id
    session.commit.assert_called_once()


# ── get_project_tags ──────────────────────────────────────────────────────────

async def test_get_project_tags_no_search():
    session = make_session()
    tags = [MagicMock(), MagicMock()]
    session.execute.return_value = make_result(scalars_list=tags)

    rules = ProjectRules(session)
    result = await rules.get_project_tags(project_id=1)
    assert result == tags


async def test_get_project_tags_with_search():
    session = make_session()
    tags = [MagicMock()]
    session.execute.return_value = make_result(scalars_list=tags)

    rules = ProjectRules(session)
    result = await rules.get_project_tags(project_id=1, search="bug")
    assert result == tags


# ── invite_users_by_email ─────────────────────────────────────────────────────

async def test_invite_users_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = ProjectRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.invite_users_by_email(
            project_id=1, invites=[], inviter_name="Alice", current_user_id=99
        )
    assert exc.value.status_code == 403


async def test_invite_users_existing_member():
    session = make_session()
    caller_role = make_result(scalar="Admin")

    role = MagicMock()
    role.name = "User"
    role.id = 2
    roles_result = MagicMock()
    roles_result.scalars.return_value.all.return_value = [role]

    existing_ids_result = MagicMock()
    existing_ids_result.scalars.return_value.all.return_value = [5]  # user 5 already in project

    user = _make_user(user_id=5, email="already@test.com")
    user_result = make_result(scalar=user)

    session.execute = AsyncMock(side_effect=[
        caller_role, roles_result, existing_ids_result, user_result
    ])

    rules = ProjectRules(session)
    invites = [{"email": "already@test.com", "role": "User"}]
    response = await rules.invite_users_by_email(
        project_id=1, invites=invites, inviter_name="Alice", current_user_id=1
    )
    assert response.results[0].already_member is True


async def test_invite_users_new_registered_user():
    session = make_session()
    caller_role = make_result(scalar="SuperAdmin")

    role = MagicMock()
    role.name = "User"
    role.id = 2
    roles_result = MagicMock()
    roles_result.scalars.return_value.all.return_value = [role]

    existing_ids_result = MagicMock()
    existing_ids_result.scalars.return_value.all.return_value = []

    user = _make_user(user_id=10, email="new@test.com")
    user_result = make_result(scalar=user)

    session.execute = AsyncMock(side_effect=[
        caller_role, roles_result, existing_ids_result, user_result
    ])

    rules = ProjectRules(session)
    invites = [{"email": "new@test.com", "role": "User"}]
    response = await rules.invite_users_by_email(
        project_id=1, invites=invites, inviter_name="Alice", current_user_id=1
    )
    assert response.results[0].registered is True
    assert response.results[0].already_member is False
    session.add.assert_called_once()


async def test_invite_users_unregistered_sends_email():
    session = make_session()
    caller_role = make_result(scalar="Admin")

    role = MagicMock()
    role.name = "User"
    role.id = 2
    roles_result = MagicMock()
    roles_result.scalars.return_value.all.return_value = [role]

    existing_ids_result = MagicMock()
    existing_ids_result.scalars.return_value.all.return_value = []

    user_result = make_result(scalar=None)  # user not in DB

    session.execute = AsyncMock(side_effect=[
        caller_role, roles_result, existing_ids_result, user_result
    ])

    rules = ProjectRules(session)
    invites = [{"email": "ghost@test.com", "role": "User"}]

    with patch("rules.project.send_email") as mock_email:
        response = await rules.invite_users_by_email(
            project_id=1, invites=invites, inviter_name="Alice", current_user_id=1
        )
    mock_email.assert_called_once()
    assert response.results[0].registered is False

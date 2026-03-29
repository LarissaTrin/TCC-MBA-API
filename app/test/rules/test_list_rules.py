"""Tests for app/rules/list.py — ListRules."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

from rules.list import ListRules
from schemas.list_schema import ListSchemaUp
from app.test.rules.conftest import make_session, make_result


def _make_list(list_id=1, project_id=10, name="To Do", order=1, cards=None):
    lst = MagicMock()
    lst.id = list_id
    lst.project_id = project_id
    lst.name = name
    lst.order = order
    lst.cards = cards if cards is not None else []
    lst.is_final = False
    return lst


# ── _check_manage_permission ──────────────────────────────────────────────────

async def test_check_manage_permission_allowed():
    session = make_session()
    session.execute.return_value = make_result(scalar="Admin")
    rules = ListRules(session)
    # Should not raise
    await rules._check_manage_permission(project_id=1, user_id=1)


async def test_check_manage_permission_leader_allowed():
    session = make_session()
    session.execute.return_value = make_result(scalar="Leader")
    rules = ListRules(session)
    await rules._check_manage_permission(project_id=1, user_id=1)


async def test_check_manage_permission_denied():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = ListRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules._check_manage_permission(project_id=1, user_id=99)
    assert exc.value.status_code == 403


# ── _check_delete_permission ──────────────────────────────────────────────────

async def test_check_delete_permission_super_admin_allowed():
    session = make_session()
    session.execute.return_value = make_result(scalar="SuperAdmin")
    rules = ListRules(session)
    await rules._check_delete_permission(project_id=1, user_id=1)


async def test_check_delete_permission_denied():
    session = make_session()
    session.execute.return_value = make_result(scalar="Leader")
    rules = ListRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules._check_delete_permission(project_id=1, user_id=99)
    assert exc.value.status_code == 403


# ── get_lists_slim ────────────────────────────────────────────────────────────

async def test_get_lists_slim_returns_list():
    session = make_session()
    lists = [_make_list(1), _make_list(2)]
    session.execute.return_value = make_result(scalars_list=lists)
    rules = ListRules(session)

    result = await rules.get_lists_slim(project_id=10)
    assert result == lists


async def test_get_lists_slim_empty():
    session = make_session()
    session.execute.return_value = make_result(scalars_list=[])
    rules = ListRules(session)

    result = await rules.get_lists_slim(project_id=10)
    assert result == []


# ── get_cards_for_list_paginated ──────────────────────────────────────────────

async def test_get_cards_for_list_paginated():
    session = make_session()
    count_result = MagicMock()
    count_result.scalar.return_value = 2
    cards = [MagicMock(), MagicMock()]
    cards_result = make_result(scalars_list=cards)

    session.execute = AsyncMock(side_effect=[count_result, cards_result])
    rules = ListRules(session)

    result = await rules.get_cards_for_list_paginated(list_id=1, page=1, limit=20)
    assert result["total"] == 2
    assert result["cards"] == cards
    assert result["page"] == 1
    assert result["has_more"] is False


async def test_get_cards_for_list_paginated_has_more():
    session = make_session()
    count_result = MagicMock()
    count_result.scalar.return_value = 50

    cards = [MagicMock() for _ in range(10)]
    cards_result = make_result(scalars_list=cards)

    session.execute = AsyncMock(side_effect=[count_result, cards_result])
    rules = ListRules(session)

    result = await rules.get_cards_for_list_paginated(list_id=1, page=1, limit=10)
    assert result["has_more"] is True


# ── get_lists_for_project ─────────────────────────────────────────────────────

async def test_get_lists_for_project():
    session = make_session()
    lists = [_make_list(1), _make_list(2)]
    session.execute.return_value = make_result(scalars_list=lists)
    rules = ListRules(session)

    result = await rules.get_lists_for_project(project_id=10)
    assert result == lists


# ── add_list ──────────────────────────────────────────────────────────────────

async def test_add_list_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = ListRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.add_list(project_id=1, data=ListSchemaUp(name="X", order=1), user_id=99)
    assert exc.value.status_code == 403


async def test_add_list_success():
    session = make_session()
    # permission check → Admin; _recalculate calls → lists
    perm_result = make_result(scalar="Admin")
    lists = [_make_list(1, order=1), _make_list(2, order=2)]
    lists_result = make_result(scalars_list=lists)

    session.execute = AsyncMock(side_effect=[perm_result, lists_result, AsyncMock(), AsyncMock()])

    rules = ListRules(session)
    new_list = await rules.add_list(
        project_id=1, data=ListSchemaUp(name="New", order=3), user_id=1
    )

    session.add.assert_called()
    session.commit.assert_called()


# ── update_list ───────────────────────────────────────────────────────────────

async def test_update_list_not_found_raises():
    session = make_session()
    perm_result = make_result(scalar="Admin")
    not_found = make_result(scalar=None)
    session.execute = AsyncMock(side_effect=[perm_result, not_found])

    rules = ListRules(session)
    with pytest.raises(NoResultFound):
        await rules.update_list(
            project_id=1, list_id=99,
            data=ListSchemaUp(name="X", order=1), user_id=1
        )


async def test_update_list_success():
    session = make_session()
    lst = _make_list()
    perm_result = make_result(scalar="Admin")
    list_result = make_result(scalar=lst)
    lists_result = make_result(scalars_list=[lst])

    session.execute = AsyncMock(side_effect=[perm_result, list_result, lists_result,
                                              AsyncMock(), AsyncMock()])

    rules = ListRules(session)
    result = await rules.update_list(
        project_id=1, list_id=1,
        data=ListSchemaUp(name="Updated", order=2), user_id=1
    )

    assert lst.name == "Updated"
    assert lst.order == 2


# ── delete_list ───────────────────────────────────────────────────────────────

async def test_delete_list_not_found_raises():
    session = make_session()
    perm_result = make_result(scalar="Admin")
    not_found = make_result(scalar=None)
    session.execute = AsyncMock(side_effect=[perm_result, not_found])

    rules = ListRules(session)
    with pytest.raises(NoResultFound):
        await rules.delete_list(project_id=1, list_id=99, user_id=1)


async def test_delete_list_no_cards_success():
    session = make_session()
    lst = _make_list(cards=[])

    perm_result = make_result(scalar="Admin")
    list_result = make_result(scalar=lst)
    lists_result = make_result(scalars_list=[lst])

    session.execute = AsyncMock(side_effect=[perm_result, list_result, lists_result,
                                              AsyncMock(), AsyncMock()])
    rules = ListRules(session)
    await rules.delete_list(project_id=1, list_id=1, user_id=1)

    session.delete.assert_called_once_with(lst)
    session.commit.assert_called()


async def test_delete_list_with_cards_no_predecessor_raises():
    session = make_session()
    card = MagicMock()
    lst = _make_list(cards=[card], order=1)

    perm_result = make_result(scalar="Admin")
    list_result = make_result(scalar=lst)
    # auto-pick predecessor: returns None (no predecessor)
    pred_result = make_result(scalar=None)

    session.execute = AsyncMock(side_effect=[perm_result, list_result, pred_result])
    rules = ListRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.delete_list(project_id=1, list_id=1, user_id=1)
    assert exc.value.status_code == 409


async def test_delete_list_with_cards_target_list_id_success():
    session = make_session()
    card = MagicMock()
    lst = _make_list(list_id=1, cards=[card], order=2)
    target_list_id = 99

    perm_result = make_result(scalar="Admin")
    list_result = make_result(scalar=lst)
    target_result = make_result(scalar=target_list_id)
    # update cards
    update_result = MagicMock()
    # _recalculate_final_list: lists query
    recalc_lists = make_result(scalars_list=[lst])
    # _recalculate_final_list: update non-final cards + update final cards
    upd1 = MagicMock()
    upd2 = MagicMock()

    session.execute = AsyncMock(
        side_effect=[perm_result, list_result, target_result,
                     update_result, recalc_lists, upd1, upd2]
    )
    session.refresh = AsyncMock()

    rules = ListRules(session)
    await rules.delete_list(project_id=1, list_id=1, user_id=1, target_list_id=target_list_id)
    session.delete.assert_called_once_with(lst)


async def test_delete_list_with_cards_invalid_target_raises():
    session = make_session()
    card = MagicMock()
    lst = _make_list(list_id=1, cards=[card], order=2)

    perm_result = make_result(scalar="Admin")
    list_result = make_result(scalar=lst)
    # target list not found in project
    target_result = make_result(scalar=None)

    session.execute = AsyncMock(side_effect=[perm_result, list_result, target_result])
    rules = ListRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.delete_list(project_id=1, list_id=1, user_id=1, target_list_id=999)
    assert exc.value.status_code == 400

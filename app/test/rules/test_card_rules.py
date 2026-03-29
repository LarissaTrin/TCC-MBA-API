"""Tests for app/rules/card.py — CardRules."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

from rules.card import CardRules
from schemas.card_schema import CardSchemaBase, CardSchemaUp, CardReorderItem
from app.test.rules.conftest import make_session, make_result


def _make_card(card_id=1, title="Task", list_id=10, card_number=1):
    c = MagicMock()
    c.id = card_id
    c.title = title
    c.list_id = list_id
    c.card_number = card_number
    c.priority = None
    c.date = None
    c.user_id = None
    c.approvers = []
    c.tasks_card = []
    c.completed_at = None
    c.sort_order = None
    return c


def _make_list_obj(list_id=10, project_id=1, name="To Do", is_final=False):
    lst = MagicMock()
    lst.id = list_id
    lst.project_id = project_id
    lst.name = name
    lst.is_final = is_final
    return lst


# ── _get_card_or_404 ──────────────────────────────────────────────────────────

async def test_get_card_or_404_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = CardRules(session)

    with pytest.raises(NoResultFound):
        await rules._get_card_or_404(card_id=99)


async def test_get_card_or_404_found():
    session = make_session()
    card = _make_card()
    session.execute.return_value = make_result(scalar=card)
    rules = CardRules(session)

    result = await rules._get_card_or_404(card_id=1)
    assert result is card


# ── get_card_by_id ────────────────────────────────────────────────────────────

async def test_get_card_by_id_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = CardRules(session)

    with pytest.raises(NoResultFound):
        await rules.get_card_by_id(card_id=99)


async def test_get_card_by_id_success():
    session = make_session()
    card = _make_card()
    session.execute.return_value = make_result(scalar=card)
    rules = CardRules(session)

    result = await rules.get_card_by_id(card_id=1)
    assert result is card


# ── add_card ──────────────────────────────────────────────────────────────────

async def test_add_card_list_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = CardRules(session)

    data = CardSchemaBase(title="New Task")
    with pytest.raises(NoResultFound):
        await rules.add_card(list_id=99, card_data=data)


async def test_add_card_success():
    session = make_session()
    lst = _make_list_obj()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 5

    session.execute = AsyncMock(side_effect=[
        make_result(scalar=lst),  # list query
        count_result,             # count cards
    ])

    rules = CardRules(session)
    data = CardSchemaBase(title="New Task")
    await rules.add_card(list_id=10, card_data=data)

    session.add.assert_called()
    session.commit.assert_called()


async def test_add_card_exception_rollbacks():
    session = make_session()
    lst = _make_list_obj()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0

    session.execute = AsyncMock(side_effect=[make_result(scalar=lst), count_result])
    session.flush = AsyncMock(side_effect=RuntimeError("db error"))

    rules = CardRules(session)
    data = CardSchemaBase(title="Task")
    with pytest.raises(RuntimeError):
        await rules.add_card(list_id=10, card_data=data)
    session.rollback.assert_called_once()


# ── _check_delete_permission ──────────────────────────────────────────────────

async def test_check_delete_permission_allowed():
    session = make_session()
    session.execute.return_value = make_result(scalar="Admin")
    rules = CardRules(session)
    # Should not raise
    await rules._check_delete_permission(card_id=1, user_id=1)


async def test_check_delete_permission_denied():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = CardRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules._check_delete_permission(card_id=1, user_id=99)
    assert exc.value.status_code == 403


# ── delete_card ───────────────────────────────────────────────────────────────

async def test_delete_card_no_permission_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar="User")
    rules = CardRules(session)

    with pytest.raises(HTTPException):
        await rules.delete_card(card_id=1, user_id=99)


async def test_delete_card_success():
    session = make_session()
    card = _make_card()
    perm_result = make_result(scalar="SuperAdmin")
    card_result = make_result(scalar=card)
    session.execute = AsyncMock(side_effect=[perm_result, card_result])

    rules = CardRules(session)
    await rules.delete_card(card_id=1, user_id=1)

    session.delete.assert_called_once_with(card)
    session.commit.assert_called_once()


# ── bulk_reorder ──────────────────────────────────────────────────────────────

async def test_bulk_reorder_empty_list_does_nothing():
    session = make_session()
    rules = CardRules(session)
    await rules.bulk_reorder([])
    session.execute.assert_not_called()


async def test_bulk_reorder_updates_sort_order():
    session = make_session()
    card = _make_card(card_id=1)
    session.execute.return_value = make_result(scalars_list=[card])

    rules = CardRules(session)
    items = [CardReorderItem(card_id=1, sort_order=3)]
    await rules.bulk_reorder(items)

    assert card.sort_order == 3
    session.commit.assert_called_once()


# ── get_card_history ──────────────────────────────────────────────────────────

async def test_get_card_history_returns_list():
    session = make_session()
    history = [MagicMock(), MagicMock()]
    r = MagicMock()
    r.scalars.return_value.all.return_value = history
    session.execute.return_value = r

    rules = CardRules(session)
    result = await rules.get_card_history(card_id=1)
    assert result == history


# ── search_cards ──────────────────────────────────────────────────────────────

async def test_search_cards_no_project():
    session = make_session()
    card = _make_card(card_number=3, title="Fix bug")
    session.execute.return_value = make_result(scalars_list=[card])

    rules = CardRules(session)
    results = await rules.search_cards(q="bug", project_id=None)
    assert len(results) == 1
    assert results[0].title == "Fix bug"


async def test_search_cards_with_project():
    session = make_session()
    card = _make_card(card_number=1, title="Deploy")
    session.execute.return_value = make_result(scalars_list=[card])

    rules = CardRules(session)
    results = await rules.search_cards(q="Deploy", project_id=5)
    assert len(results) == 1


# ── add_dependency ────────────────────────────────────────────────────────────

async def test_add_dependency_same_card_raises():
    session = make_session()
    rules = CardRules(session)

    with pytest.raises(HTTPException) as exc:
        await rules.add_dependency(card_id=1, related_card_id=1)
    assert exc.value.status_code == 400


async def test_add_dependency_already_exists_raises():
    session = make_session()
    existing_dep = MagicMock()
    r = MagicMock()
    r.scalars.return_value.first.return_value = existing_dep
    session.execute.return_value = r

    rules = CardRules(session)
    with pytest.raises(HTTPException) as exc:
        await rules.add_dependency(card_id=1, related_card_id=2)
    assert exc.value.status_code == 400


async def test_add_dependency_success():
    session = make_session()
    no_dep = MagicMock()
    no_dep.scalars.return_value.first.return_value = None

    related_card = _make_card(card_id=2, card_number=2, title="Related")
    card_result = make_result(scalar=related_card)

    session.execute = AsyncMock(side_effect=[no_dep, card_result])

    rules = CardRules(session)
    await rules.add_dependency(card_id=1, related_card_id=2, user_id=1)

    session.commit.assert_called_once()


# ── remove_dependency ─────────────────────────────────────────────────────────

async def test_remove_dependency_success():
    session = make_session()
    related = _make_card(card_id=2, card_number=2, title="Dep")
    card_result = make_result(scalar=related)
    delete_result = MagicMock()

    session.execute = AsyncMock(side_effect=[card_result, delete_result])
    rules = CardRules(session)

    await rules.remove_dependency(card_id=1, related_card_id=2, user_id=1)
    session.commit.assert_called_once()


async def test_remove_dependency_related_not_found():
    session = make_session()
    not_found = make_result(scalar=None)
    delete_result = MagicMock()

    session.execute = AsyncMock(side_effect=[not_found, delete_result])
    rules = CardRules(session)

    # Should not raise — just skips history entry
    await rules.remove_dependency(card_id=1, related_card_id=99, user_id=1)
    session.commit.assert_called_once()


# ── update_card ───────────────────────────────────────────────────────────────

async def test_update_card_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)
    rules = CardRules(session)

    with pytest.raises(NoResultFound):
        await rules.update_card(card_id=99, data=CardSchemaUp(), user_id=1)


async def test_update_card_simple_fields():
    session = make_session()
    card = _make_card()
    session.execute.return_value = make_result(scalar=card)

    rules = CardRules(session)
    data = CardSchemaUp(title="Updated Title")
    result = await rules.update_card(card_id=1, data=data, user_id=1)

    assert card.title == "Updated Title"
    session.commit.assert_called_once()


async def test_update_card_move_to_final_list():
    session = make_session()
    card = _make_card(list_id=1)
    old_list = _make_list_obj(list_id=1, name="In Progress", is_final=False)
    new_list = _make_list_obj(list_id=2, name="Done", is_final=True)

    card_result = make_result(scalar=card)
    old_list_result = make_result(scalar=old_list)
    new_list_result = make_result(scalar=new_list)

    session.execute = AsyncMock(side_effect=[card_result, old_list_result, new_list_result])

    rules = CardRules(session)
    data = CardSchemaUp(list_id=2)
    await rules.update_card(card_id=1, data=data, user_id=1)

    assert card.completed_at is not None

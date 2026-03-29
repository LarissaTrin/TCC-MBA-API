"""Tests for app/rules/comments.py — CommentRules."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import NoResultFound

from rules.comments import CommentRules
from app.test.rules.conftest import make_session, make_result
from schemas.comment_schema import CommentCreateSchema


def _make_comment(comment_id=1, user_id=10, description="hello"):
    c = MagicMock()
    c.id = comment_id
    c.user_id = user_id
    c.description = description
    return c


def _make_card(card_id=1):
    c = MagicMock()
    c.id = card_id
    return c


# ── add_comment ───────────────────────────────────────────────────────────────

async def test_add_comment_card_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = CommentRules(session)
    data = CommentCreateSchema(description="test")
    with pytest.raises(NoResultFound):
        await rules.add_comment(card_id=99, comment_data=data, user_id=1)


async def test_add_comment_success():
    session = make_session()
    card = _make_card(card_id=1)
    session.execute.return_value = make_result(scalar=card)

    comment = _make_comment()
    session.refresh = AsyncMock(side_effect=lambda obj: None)

    rules = CommentRules(session)
    data = CommentCreateSchema(description="A comment")
    result = await rules.add_comment(card_id=1, comment_data=data, user_id=10)

    session.add.assert_called_once()
    session.commit.assert_called_once()


# ── update_comment ────────────────────────────────────────────────────────────

async def test_update_comment_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = CommentRules(session)
    with pytest.raises(NoResultFound):
        await rules.update_comment(comment_id=99, new_description="x", user_id=1)


async def test_update_comment_wrong_user_raises():
    session = make_session()
    comment = _make_comment(user_id=5)
    session.execute.return_value = make_result(scalar=comment)

    rules = CommentRules(session)
    with pytest.raises(PermissionError):
        await rules.update_comment(comment_id=1, new_description="x", user_id=99)


async def test_update_comment_success():
    session = make_session()
    comment = _make_comment(user_id=10)
    session.execute.return_value = make_result(scalar=comment)

    rules = CommentRules(session)
    result = await rules.update_comment(comment_id=1, new_description="updated", user_id=10)

    assert comment.description == "updated"
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


# ── delete_comment ────────────────────────────────────────────────────────────

async def test_delete_comment_not_found_raises():
    session = make_session()
    session.execute.return_value = make_result(scalar=None)

    rules = CommentRules(session)
    with pytest.raises(NoResultFound):
        await rules.delete_comment(comment_id=99, user_id=1)


async def test_delete_comment_wrong_user_raises():
    session = make_session()
    comment = _make_comment(user_id=5)
    session.execute.return_value = make_result(scalar=comment)

    rules = CommentRules(session)
    with pytest.raises(PermissionError):
        await rules.delete_comment(comment_id=1, user_id=99)


async def test_delete_comment_success():
    session = make_session()
    comment = _make_comment(user_id=10)
    session.execute.return_value = make_result(scalar=comment)

    rules = CommentRules(session)
    await rules.delete_comment(comment_id=1, user_id=10)

    session.delete.assert_called_once_with(comment)
    session.commit.assert_called_once()

import pytest
from datetime import datetime

from schemas.comment_schema import (
    CommentCreateSchema,
    CommentSchema,
    CommentSchemaBase,
)


# ── CommentSchemaBase ─────────────────────────────────────────────────────────


def test_comment_schema_base_all_none():
    schema = CommentSchemaBase()
    # id and description are None → filtered by CustomBaseModel.dict()
    assert schema.dict() == {}


def test_comment_schema_base_with_id_and_description():
    schema = CommentSchemaBase(id=1, description="A comment")
    result = schema.dict()
    assert result["id"] == 1
    assert result["description"] == "A comment"


def test_comment_schema_base_only_description():
    schema = CommentSchemaBase(description="Hello")
    result = schema.dict()
    assert result["description"] == "Hello"
    assert "id" not in result


# ── CommentCreateSchema ───────────────────────────────────────────────────────


def test_comment_create_schema_required():
    schema = CommentCreateSchema(description="New comment")
    result = schema.dict()
    assert result["description"] == "New comment"
    assert "card_id" not in result
    assert "id" not in result


def test_comment_create_schema_with_card_id():
    schema = CommentCreateSchema(description="Fix noted", card_id=5)
    result = schema.dict()
    assert result["description"] == "Fix noted"
    assert result["card_id"] == 5


def test_comment_create_schema_missing_description():
    with pytest.raises(Exception):
        CommentCreateSchema()


# ── CommentSchema ─────────────────────────────────────────────────────────────


def test_comment_schema_all_optional_absent():
    schema = CommentSchema()
    # All fields None → filtered
    assert schema.dict() == {}


def test_comment_schema_with_timestamps():
    created = datetime(2025, 1, 10, 9, 0, 0)
    updated = datetime(2025, 1, 11, 10, 30, 0)
    schema = CommentSchema(
        id=3,
        description="Updated comment",
        created_at=created,
        updated_at=updated,
    )
    result = schema.dict()
    assert result["id"] == 3
    assert result["description"] == "Updated comment"
    assert result["created_at"] == created
    assert result["updated_at"] == updated


def test_comment_schema_no_updated_at():
    created = datetime(2025, 3, 1, 8, 0, 0)
    schema = CommentSchema(id=1, description="First post", created_at=created)
    result = schema.dict()
    assert result["created_at"] == created
    assert "updated_at" not in result
    assert "user" not in result

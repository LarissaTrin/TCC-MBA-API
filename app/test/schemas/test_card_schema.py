import pytest
from datetime import datetime

from schemas.card_schema import (
    CardDependenciesResponse,
    CardDependencyItem,
    CardHistorySchema,
    CardSchema,
    CardSchemaBase,
    CardSchemaUp,
    CardSearchResult,
)


# ── CardSchemaBase ────────────────────────────────────────────────────────────


def test_card_schema_base_title():
    card = CardSchemaBase(title="Fix login bug")
    assert card.dict() == {"title": "Fix login bug"}


def test_card_schema_base_requires_title():
    with pytest.raises(Exception):
        CardSchemaBase()


# ── CardSchemaUp ──────────────────────────────────────────────────────────────


def test_card_schema_up_all_none():
    schema = CardSchemaUp()
    result = schema.dict()
    # All fields are None → filtered by CustomBaseModel.dict()
    assert result == {}


def test_card_schema_up_partial():
    schema = CardSchemaUp(title="New title", priority=3, story_points=5)
    result = schema.dict()
    assert result["title"] == "New title"
    assert result["priority"] == 3
    assert result["story_points"] == 5
    assert "user_id" not in result
    assert "description" not in result


def test_card_schema_up_with_list_id():
    schema = CardSchemaUp(list_id=7)
    result = schema.dict()
    assert result["list_id"] == 7


# ── CardSchema ────────────────────────────────────────────────────────────────


def test_card_schema_required_fields():
    now = datetime.now()
    schema = CardSchema(id=1, card_number=3, title="Deploy v2", created_at=now)
    result = schema.dict()
    assert result["id"] == 1
    assert result["card_number"] == 3
    assert result["title"] == "Deploy v2"
    assert result["created_at"] == now


def test_card_schema_optional_absent():
    now = datetime.now()
    schema = CardSchema(id=2, card_number=1, title="Task", created_at=now)
    result = schema.dict()
    assert "user" not in result
    assert "updated_at" not in result
    assert "completed_at" not in result
    assert "description" not in result
    assert "priority" not in result


def test_card_schema_with_priority_and_hours():
    now = datetime.now()
    schema = CardSchema(
        id=5,
        card_number=2,
        title="Build feature",
        created_at=now,
        priority=2,
        planned_hours=8,
        completed_hours=3,
        story_points=5,
    )
    result = schema.dict()
    assert result["priority"] == 2
    assert result["planned_hours"] == 8
    assert result["completed_hours"] == 3
    assert result["story_points"] == 5


# ── CardHistorySchema ─────────────────────────────────────────────────────────


def test_card_history_schema_full():
    now = datetime.now()
    schema = CardHistorySchema(
        id=1,
        action="moved",
        old_value="Backlog",
        new_value="In Progress",
        created_at=now,
    )
    result = schema.dict()
    assert result["id"] == 1
    assert result["action"] == "moved"
    assert result["old_value"] == "Backlog"
    assert result["new_value"] == "In Progress"
    assert result["created_at"] == now


def test_card_history_schema_no_values():
    now = datetime.now()
    schema = CardHistorySchema(id=2, action="created", created_at=now)
    result = schema.dict()
    assert result["action"] == "created"
    assert "old_value" not in result
    assert "new_value" not in result


# ── CardDependencyItem ────────────────────────────────────────────────────────


def test_card_dependency_item():
    item = CardDependencyItem(id=10, card_number=5, title="Auth service")
    result = item.dict()
    assert result == {"id": 10, "card_number": 5, "title": "Auth service"}


# ── CardDependenciesResponse ──────────────────────────────────────────────────


def test_card_dependencies_response_empty():
    schema = CardDependenciesResponse(dependencies=[])
    assert schema.dict() == {"dependencies": []}


def test_card_dependencies_response_with_items():
    items = [
        CardDependencyItem(id=1, card_number=1, title="Setup DB"),
        CardDependencyItem(id=2, card_number=2, title="Create API"),
    ]
    schema = CardDependenciesResponse(dependencies=items)
    result = schema.dict()
    assert len(result["dependencies"]) == 2
    assert result["dependencies"][0]["title"] == "Setup DB"
    assert result["dependencies"][1]["card_number"] == 2


# ── CardSearchResult ──────────────────────────────────────────────────────────


def test_card_search_result():
    schema = CardSearchResult(id=7, card_number=12, title="Implement login")
    result = schema.dict()
    assert result == {"id": 7, "card_number": 12, "title": "Implement login"}

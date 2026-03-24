import pytest

from schemas.tasks_card_schema import TaskCardSchema, TaskCardSchemaBase


# ── TaskCardSchemaBase ────────────────────────────────────────────────────────


def test_task_card_schema_base_all_none():
    schema = TaskCardSchemaBase()
    result = schema.dict()
    # completed defaults to False (not None) so it is present; all others are None → filtered
    assert result == {"completed": False}


def test_task_card_schema_base_completed_defaults_false():
    schema = TaskCardSchemaBase(id=1, title="Write tests")
    result = schema.dict()
    assert result["id"] == 1
    assert result["title"] == "Write tests"
    assert result["completed"] is False


def test_task_card_schema_base_with_all_fields():
    schema = TaskCardSchemaBase(
        id=2, title="Deploy", date="2025-12-01", completed=True, user_id=7
    )
    result = schema.dict()
    assert result["id"] == 2
    assert result["title"] == "Deploy"
    assert result["date"] == "2025-12-01"
    assert result["completed"] is True
    assert result["user_id"] == 7


def test_task_card_schema_base_partial():
    schema = TaskCardSchemaBase(title="Review PR")
    result = schema.dict()
    assert result["title"] == "Review PR"
    assert "id" not in result
    assert "user_id" not in result


# ── TaskCardSchema ────────────────────────────────────────────────────────────


def test_task_card_schema_required_fields():
    schema = TaskCardSchema(id=1, completed=False)
    result = schema.dict()
    assert result["id"] == 1
    assert result["completed"] is False


def test_task_card_schema_missing_id():
    with pytest.raises(Exception):
        TaskCardSchema(completed=True)


def test_task_card_schema_optional_absent():
    schema = TaskCardSchema(id=3, completed=True)
    result = schema.dict()
    assert "title" not in result
    assert "date" not in result
    assert "user" not in result


def test_task_card_schema_with_user():
    from schemas.user_schema import UserSchemaBase

    user = UserSchemaBase(
        id=10,
        username="alice",
        first_name="Alice",
        last_name="Smith",
        email="alice@mail.com",
    )
    schema = TaskCardSchema(id=5, title="Review", completed=False, user=user)
    result = schema.dict()
    assert result["title"] == "Review"
    assert result["user"]["username"] == "alice"

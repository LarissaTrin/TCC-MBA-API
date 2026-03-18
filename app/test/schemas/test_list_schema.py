import pytest

from schemas.list_schema import (
    ListSchema,
    ListSchemaBase,
    ListSchemaProject,
    ListSchemaUp,
)


# ── ListSchemaBase ────────────────────────────────────────────────────────────


def test_list_schema_base_required_fields():
    schema = ListSchemaBase(name="Backlog", order=0)
    result = schema.dict()
    assert result["name"] == "Backlog"
    assert result["order"] == 0
    assert result["is_final"] is False


def test_list_schema_base_is_final_true():
    schema = ListSchemaBase(name="Done", order=3, is_final=True)
    assert schema.dict()["is_final"] is True


def test_list_schema_base_missing_required():
    with pytest.raises(Exception):
        ListSchemaBase(order=1)

    with pytest.raises(Exception):
        ListSchemaBase(name="In Progress")


# ── ListSchemaUp ──────────────────────────────────────────────────────────────


def test_list_schema_up_all_none():
    schema = ListSchemaUp()
    # All None → filtered by CustomBaseModel.dict()
    assert schema.dict() == {}


def test_list_schema_up_partial():
    schema = ListSchemaUp(name="Renamed", order=2)
    result = schema.dict()
    assert result["name"] == "Renamed"
    assert result["order"] == 2
    assert "is_final" not in result


def test_list_schema_up_is_final():
    schema = ListSchemaUp(id=5, is_final=True)
    result = schema.dict()
    assert result["id"] == 5
    assert result["is_final"] is True


# ── ListSchema ────────────────────────────────────────────────────────────────


def test_list_schema_no_cards():
    schema = ListSchema(id=1, name="Todo", order=0)
    result = schema.dict()
    assert result["id"] == 1
    assert result["name"] == "Todo"
    assert result["order"] == 0
    assert result["is_final"] is False
    # cards defaults to [] → present in dict as empty list
    assert result["cards"] == []


def test_list_schema_is_final():
    schema = ListSchema(id=3, name="Done", order=2, is_final=True)
    result = schema.dict()
    assert result["is_final"] is True
    assert result["id"] == 3


# ── ListSchemaProject ─────────────────────────────────────────────────────────


def test_list_schema_project():
    schema = ListSchemaProject(id=10, name="In Review", order=1, project_id=42)
    result = schema.dict()
    assert result["id"] == 10
    assert result["name"] == "In Review"
    assert result["order"] == 1
    assert result["project_id"] == 42
    assert result["is_final"] is False


def test_list_schema_project_is_final():
    schema = ListSchemaProject(id=2, name="Released", order=4, is_final=True, project_id=7)
    result = schema.dict()
    assert result["is_final"] is True
    assert result["project_id"] == 7

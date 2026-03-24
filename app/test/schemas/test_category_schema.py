import pytest

from schemas.category_schema import CategorySchema


# ── CategorySchema ────────────────────────────────────────────────────────────


def test_category_schema_required_fields():
    schema = CategorySchema(id=1, name="Bug")
    result = schema.dict()
    assert result["id"] == 1
    assert result["name"] == "Bug"


def test_category_schema_different_names():
    schema = CategorySchema(id=5, name="Feature")
    assert schema.dict()["name"] == "Feature"


def test_category_schema_missing_id():
    with pytest.raises(Exception):
        CategorySchema(name="Bug")


def test_category_schema_missing_name():
    with pytest.raises(Exception):
        CategorySchema(id=1)

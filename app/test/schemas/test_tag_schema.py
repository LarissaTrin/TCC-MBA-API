import pytest

from schemas.tag_schema import TagSchema, TagSchemaBase
from schemas.tag_card_schema import TagCardSchema, TagCardSchemaBase


# ── TagSchemaBase ─────────────────────────────────────────────────────────────


def test_tag_schema_base_all_none():
    tag = TagSchemaBase()
    assert tag.dict() == {}


def test_tag_schema_base_with_id_and_name():
    tag = TagSchemaBase(id=1, name="bug")
    result = tag.dict()
    assert result["id"] == 1
    assert result["name"] == "bug"


def test_tag_schema_base_name_is_string():
    tag = TagSchemaBase(id=2, name="feature")
    assert isinstance(tag.name, str)


def test_tag_schema_base_name_only():
    tag = TagSchemaBase(name="urgent")
    result = tag.dict()
    assert result["name"] == "urgent"
    assert "id" not in result


# ── TagSchema ─────────────────────────────────────────────────────────────────


def test_tag_schema_requires_id_and_name():
    tag = TagSchema(id=1, name="backend")
    assert tag.id == 1
    assert tag.name == "backend"


def test_tag_schema_missing_name_raises():
    with pytest.raises(Exception):
        TagSchema(id=1)


def test_tag_schema_missing_id_raises():
    with pytest.raises(Exception):
        TagSchema(name="frontend")


def test_tag_schema_dict_output():
    tag = TagSchema(id=5, name="hotfix")
    result = tag.dict()
    assert result["id"] == 5
    assert result["name"] == "hotfix"


# ── TagCardSchemaBase ─────────────────────────────────────────────────────────


def test_tag_card_schema_base_all_none():
    schema = TagCardSchemaBase()
    assert schema.dict() == {}


def test_tag_card_schema_base_with_tag_id():
    schema = TagCardSchemaBase(tag_id=3)
    result = schema.dict()
    assert result["tag_id"] == 3


def test_tag_card_schema_base_with_name():
    schema = TagCardSchemaBase(name="new-tag")
    result = schema.dict()
    assert result["name"] == "new-tag"
    assert "tag_id" not in result


def test_tag_card_schema_base_with_id_and_tag_id():
    schema = TagCardSchemaBase(id=10, tag_id=5)
    result = schema.dict()
    assert result["id"] == 10
    assert result["tag_id"] == 5


def test_tag_card_schema_base_with_all_fields():
    schema = TagCardSchemaBase(id=1, tag_id=2, name="existing-tag")
    result = schema.dict()
    assert result["id"] == 1
    assert result["tag_id"] == 2
    assert result["name"] == "existing-tag"


# ── TagCardSchema ─────────────────────────────────────────────────────────────


def test_tag_card_schema_with_nested_tag():
    tag_base = TagSchemaBase(id=7, name="ci-cd")
    schema = TagCardSchema(id=1, tag_id=7, tag=tag_base)
    result = schema.dict()
    assert result["tag_id"] == 7
    assert result["tag"]["id"] == 7
    assert result["tag"]["name"] == "ci-cd"


def test_tag_card_schema_no_nested_tag():
    schema = TagCardSchema(id=2, tag_id=3)
    result = schema.dict()
    assert result["tag_id"] == 3
    assert "tag" not in result


def test_tag_card_schema_name_for_new_tag():
    """Frontend sends name (no tag_id) when creating a new tag inline."""
    schema = TagCardSchema(name="new-project-tag")
    result = schema.dict()
    assert result["name"] == "new-project-tag"
    assert "tag_id" not in result
    assert "tag" not in result

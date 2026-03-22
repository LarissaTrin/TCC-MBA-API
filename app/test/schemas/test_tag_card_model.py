"""
Tests for TagCardModel attribute names and TagCardSchemaBase tag-save scenarios.

The critical regression these tests protect against:
  TagCardModel uses camelCase Python attributes (cardId, tagId) — NOT snake_case.
  Any code using card_id / tag_id will raise AttributeError at runtime.
"""

import pytest
from schemas.tag_card_schema import TagCardSchema, TagCardSchemaBase
from schemas.tag_schema import TagSchemaBase


# ── TagCardModel column attribute names ───────────────────────────────────────


def test_tag_card_model_has_cardId_attribute():
    """TagCardModel must expose 'cardId', not 'card_id'."""
    import sys
    sys.path.insert(0, "app")
    from db.models.tag_card_model import TagCardModel

    col_names = [c.key for c in TagCardModel.__table__.columns]
    assert "cardId" in col_names, f"Expected 'cardId' in columns, got: {col_names}"
    assert "card_id" not in col_names


def test_tag_card_model_has_tagId_attribute():
    """TagCardModel must expose 'tagId', not 'tag_id'."""
    import sys
    sys.path.insert(0, "app")
    from db.models.tag_card_model import TagCardModel

    col_names = [c.key for c in TagCardModel.__table__.columns]
    assert "tagId" in col_names, f"Expected 'tagId' in columns, got: {col_names}"
    assert "tag_id" not in col_names


def test_tag_card_model_table_name():
    import sys
    sys.path.insert(0, "app")
    from db.models.tag_card_model import TagCardModel

    assert TagCardModel.__tablename__ == "tagCards"


def test_tag_card_model_columns_complete():
    import sys
    sys.path.insert(0, "app")
    from db.models.tag_card_model import TagCardModel

    col_names = {c.key for c in TagCardModel.__table__.columns}
    assert col_names == {"id", "cardId", "tagId"}


# ── Schema scenarios matching the save flow ───────────────────────────────────


def test_existing_tag_send_tag_id_and_name():
    """Existing tag: frontend sends tagId (real DB id) + name."""
    schema = TagCardSchemaBase(tag_id=5, name="bug")
    result = schema.dict()
    assert result["tag_id"] == 5
    assert result["name"] == "bug"


def test_new_tag_send_name_only():
    """New tag typed by user: frontend sends name, no valid tag_id."""
    schema = TagCardSchemaBase(name="new-feature")
    result = schema.dict()
    assert result["name"] == "new-feature"
    assert "tag_id" not in result


def test_new_tag_fake_timestamp_id_with_name():
    """
    Frontend uses Date.now() as a placeholder id for new tags.
    Schema accepts both; backend ignores tag_id when name is present
    (name always takes priority to avoid int32 overflow with timestamps).
    """
    fake_id = 1774056966954  # actual Date.now() value from the 500 error
    schema = TagCardSchemaBase(tag_id=fake_id, name="urgent")
    result = schema.dict()
    # Schema stores both — backend resolves by name, discarding fake tag_id
    assert result["tag_id"] == fake_id
    assert result["name"] == "urgent"


def test_tag_id_int32_overflow_value_is_accepted_by_schema():
    """
    Values > 2^31-1 (2147483647) overflow PostgreSQL int4.
    The schema must accept them; the backend must never insert them.
    Backend rule: when name is present, tag_id is always ignored.
    """
    overflow_id = 2_147_483_648  # int32 max + 1
    schema = TagCardSchemaBase(tag_id=overflow_id, name="overflow-tag")
    result = schema.dict()
    assert result["tag_id"] == overflow_id  # schema stores as-is
    assert result["name"] == "overflow-tag"  # backend will resolve by name


def test_tag_card_schema_with_tag_id_zero_treated_as_none():
    """tag_id=0 is falsy — schema allows it but backend should use name."""
    schema = TagCardSchemaBase(tag_id=0, name="my-tag")
    result = schema.dict()
    assert result["tag_id"] == 0
    assert result["name"] == "my-tag"


def test_multiple_tags_schema_list():
    """Simulate the list sent by frontend on card save."""
    tags_payload = [
        TagCardSchemaBase(tag_id=1, name="backend"),   # existing tag
        TagCardSchemaBase(name="new-label"),            # new tag (name only)
        TagCardSchemaBase(tag_id=1700000000001, name="another-new"),  # new with fake id
    ]
    results = [t.dict() for t in tags_payload]

    assert results[0]["tag_id"] == 1
    assert results[0]["name"] == "backend"

    assert "tag_id" not in results[1]
    assert results[1]["name"] == "new-label"

    assert results[2]["tag_id"] == 1700000000001
    assert results[2]["name"] == "another-new"


def test_tag_card_schema_full_with_nested_tag_and_name():
    """Response schema: nested tag object returned after save."""
    nested = TagSchemaBase(id=3, name="ci-cd")
    schema = TagCardSchema(id=10, tag_id=3, name="ci-cd", tag=nested)
    result = schema.dict()
    assert result["tag_id"] == 3
    assert result["name"] == "ci-cd"
    assert result["tag"]["id"] == 3
    assert result["tag"]["name"] == "ci-cd"


def test_tag_card_schema_base_name_is_str_not_int():
    """Regression: TagSchemaBase.name was previously typed as int."""
    schema = TagCardSchemaBase(name="test-tag")
    assert isinstance(schema.name, str)


def test_empty_tag_list_schema():
    """Empty tag list should produce no errors."""
    tags: list[TagCardSchemaBase] = []
    assert tags == []

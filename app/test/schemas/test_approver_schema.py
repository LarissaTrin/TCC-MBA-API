from schemas.approver_schema import ApproverSchema, ApproverSchemaBase


# ── ApproverSchemaBase ────────────────────────────────────────────────────────


def test_approver_schema_base_all_none():
    schema = ApproverSchemaBase()
    result = schema.dict()
    assert result == {}


def test_approver_schema_base_with_values():
    schema = ApproverSchemaBase(id=1, environment="Production", user_id=42)
    result = schema.dict()
    assert result["id"] == 1
    assert result["environment"] == "Production"
    assert result["user_id"] == 42


def test_approver_schema_base_partial():
    schema = ApproverSchemaBase(environment="Staging")
    result = schema.dict()
    assert result["environment"] == "Staging"
    assert "id" not in result
    assert "user_id" not in result


# ── ApproverSchema ────────────────────────────────────────────────────────────


def test_approver_schema_no_user():
    schema = ApproverSchema(id=3, environment="QA", user_id=10)
    result = schema.dict()
    assert result["id"] == 3
    assert result["environment"] == "QA"
    assert result["user_id"] == 10
    assert "user" not in result


def test_approver_schema_all_none():
    schema = ApproverSchema()
    assert schema.dict() == {}


def test_approver_schema_with_user():
    from schemas.user_schema import UserSchemaBase

    user = UserSchemaBase(
        id=5,
        username="jdoe",
        first_name="John",
        last_name="Doe",
        email="jdoe@mail.com",
    )
    schema = ApproverSchema(id=1, environment="Prod", user_id=5, user=user)
    result = schema.dict()
    assert result["user"]["username"] == "jdoe"
    assert result["user"]["id"] == 5

import pytest
from schemas.project_user_schema import ProjectMemberSearchItem


def test_project_member_search_item_valid():
    item = ProjectMemberSearchItem(
        id=1,
        first_name="João",
        last_name="Silva",
        email="joao@empresa.com",
    )
    result = item.dict()
    assert result["id"] == 1
    assert result["first_name"] == "João"
    assert result["last_name"] == "Silva"
    assert result["email"] == "joao@empresa.com"


def test_project_member_search_item_camel_alias():
    item = ProjectMemberSearchItem(
        id=2,
        first_name="Ana",
        last_name="Costa",
        email="ana@empresa.com",
    )
    data = item.model_dump(by_alias=True)
    assert data["firstName"] == "Ana"
    assert data["lastName"] == "Costa"


def test_project_member_search_item_missing_required_field():
    with pytest.raises(Exception):
        ProjectMemberSearchItem(
            first_name="X",
            last_name="Y",
            email="x@mail.com",
        )


def test_project_member_search_item_invalid_email():
    with pytest.raises(Exception):
        ProjectMemberSearchItem(
            id=3,
            first_name="X",
            last_name="Y",
            email="not-an-email",
        )

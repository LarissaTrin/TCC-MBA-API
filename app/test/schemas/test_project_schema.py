from schemas.project_schema import ProjectSchemaBase


def test_project_schema_create():
    project = ProjectSchemaBase(title="Project 1", description="Description project 1")

    assert project.dict() == {
        "title": "Project 1",
        "description": "Description project 1",
    }

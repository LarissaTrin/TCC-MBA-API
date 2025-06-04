from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException

from app.schemas.project_schema import ProjectSchemaBase, ProjectSchemaUp
from app.schemas.project_user_schema import ProjectUserSchemaBase
from app.core.deps import get_current_user, get_session
from app.rules.project import ProjectRules
from app.schemas.user_schema import UserSchema

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectSchemaBase,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    return await rules.add_project(project, creator_id=current_user.id)


@router.get("/{project_id}")
async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    return await rules.get_project_by_id_and_user(project_id, user_id=current_user.id)


@router.get("/", response_model=list[ProjectSchemaBase])
async def get_projects(
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    return await rules.get_projects_for_user(user_id=current_user.id)


@router.put("/{project_id}")
async def update_project(
    project_id: int,
    data: ProjectSchemaUp,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    # Aqui você pode validar que o current_user tem permissão de edição se quiser
    return await rules.update_project(project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    await rules.delete_project(project_id, user_id=current_user.id)


@router.put("/{project_id}/users")
async def update_project_users(
    project_id: int,
    users: list[ProjectUserSchemaBase],
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    await rules.update_project_users(
        project_id=project_id,
        users_data=users,
        current_user_id=current_user.id,
    )
    return {"detail": "Usuários atualizados com sucesso"}

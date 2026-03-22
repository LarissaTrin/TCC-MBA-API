from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException

from app.schemas.project_schema import (
    InviteEntry,
    InviteUsersRequest,
    InviteUsersResponse,
    ProjectSchema,
    ProjectSchemaBase,
    ProjectSchemaUp,
)
from app.schemas.tag_schema import TagSchema
from app.schemas.project_user_schema import ProjectUserSchemaBase, ProjectMemberSearchItem
from app.core.deps import get_current_user, get_session
from app.rules.project import ProjectRules
from app.schemas.user_schema import UserSchema

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectSchemaBase)
async def create_project(
    project: ProjectSchemaBase,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    project_id = await rules.add_project(project, creator_id=current_user.id)
    return {"id": project_id, "title": project.title, "description": project.description}


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    project = await rules.get_project_by_id_and_user(
        project_id, user_id=current_user.id
    )
    return project


@router.get("/", response_model=list[ProjectSchemaBase])
async def get_projects(
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    return await rules.get_projects_for_user(user_id=current_user.id)


@router.put("/{project_id}", response_model=ProjectSchema)
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


@router.post("/{project_id}/members/invite", response_model=InviteUsersResponse)
async def invite_project_members(
    project_id: int,
    body: InviteUsersRequest,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    inviter_name = f"{current_user.firstName} {current_user.lastName or ''}".strip()
    invites = [{"email": inv.email, "role": inv.role} for inv in body.invites]
    return await rules.invite_users_by_email(
        project_id=project_id,
        invites=invites,
        inviter_name=inviter_name,
        current_user_id=current_user.id,
    )


@router.delete("/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    member_user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    await rules.remove_project_member(
        project_id=project_id,
        user_id_to_remove=member_user_id,
        current_user_id=current_user.id,
    )


@router.get("/{project_id}/members/search", response_model=list[ProjectMemberSearchItem])
async def search_project_members(
    project_id: int,
    q: str = Query(min_length=1),
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    rules = ProjectRules(db)
    users = await rules.search_project_members(
        project_id=project_id,
        current_user_id=current_user.id,
        query=q,
    )
    return [
        ProjectMemberSearchItem(
            id=u.id,
            first_name=u.firstName,
            last_name=u.lastName,
            email=u.email,
        )
        for u in users
    ]


@router.get("/{project_id}/tags", response_model=list[TagSchema])
async def get_project_tags(
    project_id: int,
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: UserSchema = Depends(get_current_user),
):
    """
    Retorna todas as tags do projeto. Aceita `?q=` para filtrar por nome.
    """
    rules = ProjectRules(db)
    return await rules.get_project_tags(project_id, search=q)


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

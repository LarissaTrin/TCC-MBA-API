from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from fastapi.exceptions import HTTPException
from fastapi import status

from app.core.configs import settings
from app.core.email import send_email
from app.db.models.list_model import ListModel
from app.db.models.project_model import ProjectModel
from app.db.models.project_user_model import ProjectUserModel
from app.db.models.role_model import RoleModel
from app.db.models.user_model import UserModel

from app.schemas.project_schema import (
    InviteUserResult,
    InviteUsersResponse,
    ProjectSchemaBase,
    ProjectSchemaUp,
)
from app.schemas.project_user_schema import ProjectUserSchemaBase


class ProjectRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_project(self, project: ProjectSchemaBase, creator_id: int) -> int:
        """
        Adiciona um novo projeto e insere o criador como superAdmin no projeto.

        Args:
            project (ProjectSchemaBase): Dados do projeto.
            creator_id (int): ID do usuário criador.

        Returns:
            int: ID do projeto criado.
        """
        try:
            # Criação do projeto
            project_model = ProjectModel(**project.dict(), creator_id=creator_id)
            self.db_session.add(project_model)
            await self.db_session.commit()
            await self.db_session.refresh(project_model)

            # Busca o ID da role "superAdmin"
            result = await self.db_session.execute(
                select(RoleModel.id).where(RoleModel.name == "SuperAdmin")
            )
            role_id = result.scalar_one_or_none()

            if role_id is None:
                raise ValueError("Role 'superAdmin' não encontrada.")

            # Criação da associação ProjectUser
            project_user = ProjectUserModel(
                user_id=creator_id, project_id=project_model.id, role_id=role_id
            )
            self.db_session.add(project_user)
            await self.db_session.commit()

            return project_model.id

        except Exception as e:
            await self.db_session.rollback()
            raise e

    async def get_project_by_id_and_user(
        self, project_id: int, user_id: int
    ) -> ProjectModel | None:
        """
        Busca um projeto pelo ID somente se o usuário estiver associado a ele.

        Args:
            project_id (int): ID do projeto a ser buscado.
            user_id (int): ID do usuário que deve estar associado ao projeto.

        Returns:
            ProjectModel | None: Retorna o projeto com todos os relacionamentos carregados
            se o usuário estiver associado, ou None caso contrário.

        Raises:
            NoResultFound: Se o projeto não existir ou usuário não estiver associado.
        """
        query = (
            select(ProjectModel)
            .options(
                selectinload(ProjectModel.creator),
                selectinload(ProjectModel.lists),
                selectinload(ProjectModel.project_users).selectinload(
                    ProjectUserModel.role
                ),
                selectinload(ProjectModel.project_users).selectinload(
                    ProjectUserModel.user
                ),  # <-- importante
                # selectinload(ProjectModel.tags),  # se usar tags
            )
            .join(
                ProjectModel.project_users
            )  # Assumindo relacionamento com ProjectUserModel
            .where(ProjectModel.id == project_id, ProjectUserModel.user_id == user_id)
        )

        result = await self.db_session.execute(query)
        project = result.scalars().unique().one_or_none()

        if not project:
            raise NoResultFound(
                f"Projeto com id={project_id} não encontrado para o usuário id={user_id}"
            )

        return project

    async def get_projects_for_user(self, user_id: int) -> list[ProjectModel]:
        """
        Retorna a lista de projetos associados a um usuário, apenas com id e title.

        Args:
            user_id (int): ID do usuário.

        Returns:
            list[ProjectModel]: Lista de ProjectModel com 'id' e 'title' dos projetos.
        """
        query = (
            select(ProjectModel.id, ProjectModel.title, ProjectModel.description)
            .join(ProjectModel.project_users)
            .where(ProjectUserModel.user_id == user_id)
        )

        result = await self.db_session.execute(query)
        projects: list[ProjectModel] = result.unique().all()

        return projects

    async def update_project(
        self, project_id: int, data: ProjectSchemaUp
    ) -> ProjectModel:
        """
        Atualiza um projeto existente com os dados fornecidos.

        Atualiza o título, a descrição e a lista de tarefas (lists) associadas ao projeto.
        As listas podem ser atualizadas, criadas ou removidas conforme os dados recebidos.

        Args:
            project_id (int): ID do projeto a ser atualizado.
            data (ProjectSchemaUp): Dados a serem atualizados no projeto, podendo incluir
                o título, a descrição e uma lista de tarefas com ou sem ID.

        Returns:
            ProjectModel: O modelo do projeto atualizado, com listas carregadas.

        Raises:
            Exception: Se o projeto com o ID fornecido não for encontrado.
        """
        query = (
            select(ProjectModel)
            .options(
                selectinload(ProjectModel.creator),
                selectinload(ProjectModel.lists),
                selectinload(ProjectModel.project_users).selectinload(
                    ProjectUserModel.user
                ),
                selectinload(ProjectModel.project_users).selectinload(
                    ProjectUserModel.role
                ),
            )
            .where(ProjectModel.id == project_id)
        )

        result = await self.db_session.execute(query)
        project = result.scalars().unique().one_or_none()
        if not project:
            raise Exception(f"Projeto {project_id} não encontrado")

        # Atualizar title e description
        if data.title is not None:
            project.title = data.title
        if data.description is not None:
            project.description = data.description

        # Atualizar listas
        if data.lists is not None:
            # Mapeia listas atuais por id
            existing_lists = {lst.id: lst for lst in project.lists}

            # IDs recebidos para controle do que fica/remover
            received_ids = set()

            for list_data in data.lists:
                if list_data.id is not None and list_data.id in existing_lists:
                    # Atualiza lista existente
                    existing_list = existing_lists[list_data.id]
                    existing_list.name = list_data.name
                    existing_list.order = list_data.order
                    received_ids.add(list_data.id)
                else:
                    # Cria nova lista
                    new_list = ListModel(
                        name=list_data.name,
                        order=list_data.order,
                        project_id=project_id,
                    )
                    self.db_session.add(new_list)

            # Opcional: remover listas que não foram enviadas
            for lst in project.lists:
                if lst.id not in received_ids:
                    await self.db_session.delete(lst)

        await self.db_session.commit()
        await self.db_session.refresh(project)

        return project

    async def delete_project(self, project_id: int, user_id: int) -> None:
        """
        Remove um projeto do banco de dados, desde que o usuário seja o criador.

        Args:
            project_id (int): ID do projeto a ser removido.
            user_id (int): ID do usuário solicitante.

        Raises:
            Exception: Se o projeto não existir ou o usuário não for o criador.
        """
        query = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.db_session.execute(query)
        project = result.scalars().one_or_none()

        if not project:
            raise Exception(f"Projeto com id={project_id} não encontrado.")
        if project.creator_id != user_id:
            raise Exception("Usuário não autorizado a deletar este projeto.")

        await self.db_session.delete(project)
        await self.db_session.commit()

    async def update_project_users(
        self,
        project_id: int,
        users_data: list[ProjectUserSchemaBase],
        current_user_id: int,
    ) -> None:
        """
        Atualiza os usuários associados a um projeto, permitindo apenas se o usuário atual for 'Admin' ou 'SuperAdmin'.

        Args:
            project_id (int): ID do projeto.
            users_data (list[ProjectUserSchemaBase]): Lista de usuários a adicionar/atualizar/remover.
            current_user_id (int): ID do usuário que está tentando fazer a operação.

        Raises:
            PermissionError: Se o usuário não for 'Admin' nem 'SuperAdmin'.
            Exception: Se o projeto não for encontrado.
        """
        # Verifica se o usuário atual é Admin ou SuperAdmin no projeto
        role_query = (
            select(RoleModel.name)
            .join(ProjectUserModel, RoleModel.id == ProjectUserModel.role_id)
            .where(
                ProjectUserModel.project_id == project_id,
                ProjectUserModel.user_id == current_user_id,
            )
        )
        role_result = await self.db_session.execute(role_query)
        role_name = role_result.scalar_one_or_none()

        if role_name not in {"Admin", "SuperAdmin"}:
            raise PermissionError(
                "Somente Admins ou SuperAdmins podem editar usuários do projeto."
            )

        # Carrega o projeto e seus usuários
        project_query = (
            select(ProjectModel)
            .options(selectinload(ProjectModel.project_users))
            .where(ProjectModel.id == project_id)
        )
        result = await self.db_session.execute(project_query)
        project = result.scalars().unique().one_or_none()

        if not project:
            raise Exception(f"Projeto com id={project_id} não encontrado.")

        existing_users = {user.id: user for user in project.project_users if user.id}
        received_ids = set()

        for user_data in users_data:
            if user_data.id is not None and user_data.id in existing_users:
                existing = existing_users[user_data.id]
                existing.user_id = user_data.user_id
                existing.role_id = user_data.role_id
                received_ids.add(user_data.id)
            else:
                new_user = ProjectUserModel(
                    user_id=user_data.user_id,
                    role_id=user_data.role_id,
                    project_id=project_id,
                )
                self.db_session.add(new_user)

        # Remove usuários que não foram enviados na nova lista
        for user in project.project_users:
            if user.id not in received_ids:
                await self.db_session.delete(user)

        await self.db_session.commit()

    async def _get_user_role_in_project(self, project_id: int, user_id: int) -> str | None:
        query = (
            select(RoleModel.name)
            .join(ProjectUserModel, RoleModel.id == ProjectUserModel.role_id)
            .where(
                ProjectUserModel.project_id == project_id,
                ProjectUserModel.user_id == user_id,
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def invite_users_by_email(
        self,
        project_id: int,
        invites: list[dict],  # [{"email": str, "role": str}]
        inviter_name: str,
        current_user_id: int,
    ) -> InviteUsersResponse:
        """
        Convida usuários por email para um projeto. Apenas SuperAdmin e Admin podem convidar.
        Se o email existir no banco, adiciona com o role especificado.
        Se não existir, envia email de convite.
        Roles permitidos ao convidar: User, Leader, Admin (nunca SuperAdmin).
        """
        caller_role = await self._get_user_role_in_project(project_id, current_user_id)
        if caller_role not in {"SuperAdmin", "Admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas SuperAdmin e Admin podem convidar membros.",
            )

        # Carrega todos os role_ids de uma vez
        roles_result = await self.db_session.execute(select(RoleModel))
        roles_map: dict[str, int] = {
            r.name: r.id for r in roles_result.scalars().all()
        }

        allowed_invite_roles = {"User", "Leader", "Admin"}

        # Busca membros atuais do projeto
        existing_members_result = await self.db_session.execute(
            select(ProjectUserModel.user_id).where(
                ProjectUserModel.project_id == project_id
            )
        )
        existing_user_ids = set(existing_members_result.scalars().all())

        results: list[InviteUserResult] = []

        for invite in invites:
            email = invite["email"]
            role_name = invite.get("role", "User")

            # Garante que não se pode atribuir SuperAdmin por convite
            if role_name not in allowed_invite_roles:
                role_name = "User"

            role_id = roles_map.get(role_name)
            if role_id is None:
                role_id = roles_map.get("User")

            user_result = await self.db_session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            user = user_result.scalar_one_or_none()

            if user:
                if user.id in existing_user_ids:
                    results.append(
                        InviteUserResult(email=email, registered=True, already_member=True)
                    )
                else:
                    new_member = ProjectUserModel(
                        user_id=user.id,
                        project_id=project_id,
                        role_id=role_id,
                    )
                    self.db_session.add(new_member)
                    existing_user_ids.add(user.id)
                    results.append(
                        InviteUserResult(email=email, registered=True, already_member=False)
                    )
            else:
                front_url = settings.FRONT_URL
                send_email(
                    to=email,
                    subject="Você foi convidado para o sistema de gerenciamento",
                    body=(
                        f"Olá!\n\n{inviter_name} convidou você para participar de um projeto "
                        f"no sistema de gerenciamento.\n\n"
                        f"Você ainda não possui uma conta. Crie sua conta em:\n"
                        f"{front_url}/login/register"
                    ),
                )
                results.append(
                    InviteUserResult(email=email, registered=False, already_member=False)
                )

        await self.db_session.commit()
        return InviteUsersResponse(results=results)

    async def remove_project_member(
        self, project_id: int, user_id_to_remove: int, current_user_id: int
    ) -> None:
        """
        Remove um membro do projeto. Apenas SuperAdmin e Admin podem remover.
        O SuperAdmin não pode ser removido.
        """
        role_name = await self._get_user_role_in_project(project_id, current_user_id)
        if role_name not in {"SuperAdmin", "Admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas SuperAdmin e Admin podem remover membros.",
            )

        target_role = await self._get_user_role_in_project(project_id, user_id_to_remove)
        if target_role == "SuperAdmin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O criador do projeto não pode ser removido.",
            )

        result = await self.db_session.execute(
            select(ProjectUserModel).where(
                ProjectUserModel.project_id == project_id,
                ProjectUserModel.user_id == user_id_to_remove,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membro não encontrado no projeto.",
            )

        await self.db_session.delete(member)
        await self.db_session.commit()

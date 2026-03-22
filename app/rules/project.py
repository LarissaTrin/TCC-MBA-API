from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound
from sqlalchemy import or_

from fastapi.exceptions import HTTPException
from fastapi import status

from app.core.configs import settings
from app.core.email import send_email
from app.db.models.list_model import ListModel
from app.db.models.project_model import ProjectModel
from app.db.models.tag_model import TagModel
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
        Creates a new project and adds the creator as SuperAdmin.

        Args:
            project (ProjectSchemaBase): Project data.
            creator_id (int): ID of the user creating the project.

        Returns:
            int: ID of the created project.
        """
        try:
            # Create the project
            project_model = ProjectModel(**project.dict(), creator_id=creator_id)
            self.db_session.add(project_model)
            await self.db_session.commit()
            await self.db_session.refresh(project_model)

            # Fetch the ID of the "SuperAdmin" role
            result = await self.db_session.execute(
                select(RoleModel.id).where(RoleModel.name == "SuperAdmin")
            )
            role_id = result.scalar_one_or_none()

            if role_id is None:
                raise ValueError("Role 'SuperAdmin' not found.")

            # Create the ProjectUser association
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
        Fetches a project by ID only if the user is associated with it.

        Args:
            project_id (int): ID of the project.
            user_id (int): ID of the user that must be associated with the project.

        Returns:
            ProjectModel | None: The project with all relationships loaded, or None.

        Raises:
            NoResultFound: If the project does not exist or the user is not associated.
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
                ),
                # selectinload(ProjectModel.tags),  # enable if using tags
            )
            .join(ProjectModel.project_users)
            .where(ProjectModel.id == project_id, ProjectUserModel.user_id == user_id)
        )

        result = await self.db_session.execute(query)
        project = result.scalars().unique().one_or_none()

        if not project:
            raise NoResultFound(
                f"Project id={project_id} not found for user id={user_id}"
            )

        return project

    async def get_projects_for_user(self, user_id: int) -> list[ProjectModel]:
        """
        Returns the list of projects associated with a user (id and title only).

        Args:
            user_id (int): ID of the user.

        Returns:
            list[ProjectModel]: List of ProjectModel with 'id' and 'title'.
        """
        query = (
            select(ProjectModel.id, ProjectModel.title, ProjectModel.description)
            .join(ProjectModel.project_users)
            .where(ProjectUserModel.user_id == user_id)
        )

        result = await self.db_session.execute(query)
        projects: list[ProjectModel] = result.unique().all()

        return projects

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

    async def update_project(
        self, project_id: int, data: ProjectSchemaUp, user_id: int
    ) -> ProjectModel:
        """
        Updates an existing project with the provided data.

        Updates the title, description, and lists associated with the project.
        Lists can be updated, created, or removed according to the received data.

        Args:
            project_id (int): ID of the project to update.
            data (ProjectSchemaUp): Data to update, which may include title,
                description, and a list of sections with or without IDs.

        Returns:
            ProjectModel: The updated project model with lists loaded.

        Raises:
            Exception: If the project with the given ID is not found.
        """
        role = await self._get_user_role_in_project(project_id, user_id)
        if role not in {"SuperAdmin", "Admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SuperAdmin and Admin can update project settings.",
            )

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
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Update title and description
        if data.title is not None:
            project.title = data.title
        if data.description is not None:
            project.description = data.description

        # Update lists
        if data.lists is not None:
            # Map existing lists by id
            existing_lists = {lst.id: lst for lst in project.lists}

            # Track received IDs to detect removals
            received_ids = set()

            for list_data in data.lists:
                if list_data.id is not None and list_data.id in existing_lists:
                    # Update existing list
                    existing_list = existing_lists[list_data.id]
                    existing_list.name = list_data.name
                    existing_list.order = list_data.order
                    received_ids.add(list_data.id)
                else:
                    # Create new list
                    new_list = ListModel(
                        name=list_data.name,
                        order=list_data.order,
                        project_id=project_id,
                    )
                    self.db_session.add(new_list)

            # Remove lists not included in the request
            for lst in project.lists:
                if lst.id not in received_ids:
                    await self.db_session.delete(lst)

        await self.db_session.commit()
        await self.db_session.refresh(project)

        return project

    async def delete_project(self, project_id: int, user_id: int) -> None:
        """
        Deletes a project from the database. Only the creator is allowed to do this.

        Args:
            project_id (int): ID of the project to delete.
            user_id (int): ID of the requesting user.

        Raises:
            Exception: If the project does not exist or the user is not the creator.
        """
        query = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.db_session.execute(query)
        project = result.scalars().one_or_none()

        if not project:
            raise Exception(f"Project id={project_id} not found.")
        if project.creator_id != user_id:
            raise Exception("User not authorized to delete this project.")

        await self.db_session.delete(project)
        await self.db_session.commit()

    async def update_project_users(
        self,
        project_id: int,
        users_data: list[ProjectUserSchemaBase],
        current_user_id: int,
    ) -> None:
        """
        Updates the users associated with a project. Only Admin or SuperAdmin can do this.

        Args:
            project_id (int): ID of the project.
            users_data (list[ProjectUserSchemaBase]): Users to add, update, or remove.
            current_user_id (int): ID of the user performing the operation.

        Raises:
            PermissionError: If the user is neither Admin nor SuperAdmin.
            Exception: If the project is not found.
        """
        # Check if the current user is Admin or SuperAdmin in the project
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
                "Only Admins or SuperAdmins can edit project users."
            )

        # Load project and its users
        project_query = (
            select(ProjectModel)
            .options(selectinload(ProjectModel.project_users))
            .where(ProjectModel.id == project_id)
        )
        result = await self.db_session.execute(project_query)
        project = result.scalars().unique().one_or_none()

        if not project:
            raise Exception(f"Project id={project_id} not found.")

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

        # Remove users not included in the updated list
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
        Invites users to a project by email. Only SuperAdmin and Admin can invite.
        If the email exists in the database, the user is added with the specified role.
        If not, an invitation email is sent.
        Allowed roles for invites: User, Leader, Admin (never SuperAdmin).
        """
        caller_role = await self._get_user_role_in_project(project_id, current_user_id)
        if caller_role not in {"SuperAdmin", "Admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SuperAdmin and Admin can invite members.",
            )

        # Load all role IDs at once
        roles_result = await self.db_session.execute(select(RoleModel))
        roles_map: dict[str, int] = {
            r.name: r.id for r in roles_result.scalars().all()
        }

        allowed_invite_roles = {"User", "Leader", "Admin"}

        # Fetch current project members
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

            # Ensure SuperAdmin cannot be assigned via invite
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
                    subject="You've been invited to the project management system",
                    body=(
                        f"Hello!\n\n{inviter_name} has invited you to join a project "
                        f"on the project management system.\n\n"
                        f"You don't have an account yet. Create one at:\n"
                        f"{front_url}/login/register"
                    ),
                )
                results.append(
                    InviteUserResult(email=email, registered=False, already_member=False)
                )

        await self.db_session.commit()
        return InviteUsersResponse(results=results)

    async def search_project_members(
        self, project_id: int, current_user_id: int, query: str
    ) -> list[UserModel]:
        """
        Searches project members whose name or email contains the given term.

        Args:
            project_id (int): ID of the project.
            current_user_id (int): ID of the user performing the search (must be a member).
            query (str): Search term (first name, last name, or email).

        Returns:
            list[UserModel]: Up to 10 matching users.

        Raises:
            HTTPException 403: If the user is not a project member.
        """
        member_check = await self.db_session.execute(
            select(ProjectUserModel.user_id).where(
                ProjectUserModel.project_id == project_id,
                ProjectUserModel.user_id == current_user_id,
            )
        )
        if member_check.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project.",
            )

        result = await self.db_session.execute(
            select(UserModel)
            .join(ProjectUserModel, UserModel.id == ProjectUserModel.user_id)
            .where(
                ProjectUserModel.project_id == project_id,
                or_(
                    UserModel.firstName.ilike(f"%{query}%"),
                    UserModel.lastName.ilike(f"%{query}%"),
                    UserModel.email.ilike(f"%{query}%"),
                ),
            )
            .limit(10)
        )
        return list(result.scalars().all())

    async def remove_project_member(
        self, project_id: int, user_id_to_remove: int, current_user_id: int
    ) -> None:
        """
        Removes a member from the project. Only SuperAdmin and Admin can remove members.
        The SuperAdmin (project creator) cannot be removed.
        """
        role_name = await self._get_user_role_in_project(project_id, current_user_id)
        if role_name not in {"SuperAdmin", "Admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SuperAdmin and Admin can remove members.",
            )

        target_role = await self._get_user_role_in_project(project_id, user_id_to_remove)
        if target_role == "SuperAdmin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The project creator cannot be removed.",
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
                detail="Member not found in the project.",
            )

        await self.db_session.delete(member)
        await self.db_session.commit()

    async def get_project_tags(self, project_id: int, search: str | None = None) -> list[TagModel]:
        """
        Returns all tags for a project.

        Args:
            project_id (int): ID of the project.
            search (str | None): Optional case-insensitive name filter.

        Returns:
            list[TagModel]: List of project tags.
        """
        query = select(TagModel).where(TagModel.projectId == project_id)
        if search:
            query = query.where(TagModel.name.ilike(f"%{search}%"))
        result = await self.db_session.execute(query.order_by(TagModel.name))
        return result.scalars().unique().all()

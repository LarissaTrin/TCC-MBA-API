from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.future import select

from core.configs import settings
from db.conection import engine, Session
from db.models.role_model import RoleModel


async def create_tables() -> None:
    import app.db.models.__all_models

    print("Criando as tabelas no banco de dados...")

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: sync_conn.execute(text("DROP SCHEMA public CASCADE"))
        )
        await conn.run_sync(
            lambda sync_conn: sync_conn.execute(text("CREATE SCHEMA public"))
        )
        await conn.run_sync(settings.DBBaseModel.metadata.create_all)

    print("Tabelas criadas com sucesso")

    await seed_roles()


async def seed_roles():
    async with Session() as session:
        result = await session.execute(select(RoleModel))
        roles_exist = result.scalars().first()

        if roles_exist:
            print("Roles já existem. Pulando inserção.")
            return

        print("Inserindo roles iniciais...")
        roles = [
            RoleModel(name="SuperAdmin"),
            RoleModel(name="Admin"),
            RoleModel(name="Leader"),
            RoleModel(name="User"),
        ]
        session.add_all(roles)
        await session.commit()
        print("Roles inseridos com sucesso.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_tables())

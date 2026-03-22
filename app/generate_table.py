from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.future import select

from app.core.configs import settings
from app.db.conection import engine, Session
from app.db.models.role_model import RoleModel


def _guard_against_production() -> None:
    """Impede execução acidental contra o banco de produção."""
    if not settings.TEST_MODE:
        raise RuntimeError(
            "\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║  BLOQUEADO — generate_table.py apaga TODO o banco!       ║\n"
            "║                                                          ║\n"
            "║  TEST_MODE=False indica banco de PRODUÇÃO.               ║\n"
            "║  Defina TEST_MODE=True no .env para rodar localmente.    ║\n"
            "╚══════════════════════════════════════════════════════════╝"
        )


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

    _guard_against_production()
    asyncio.run(create_tables())

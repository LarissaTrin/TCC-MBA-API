from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.configs import settings
from app.api.api import api_router
from app.db.conection import engine

app = FastAPI(title="TCC API")


@app.on_event("startup")
async def create_new_tables():
    async with engine.begin() as conn:
        # Create any brand-new tables (e.g. card_history)
        await conn.run_sync(settings.DBBaseModel.metadata.create_all)

        # Add new columns to existing tables (create_all ignores existing tables).
        # IF NOT EXISTS is safe to run on every startup.
        await conn.execute(
            text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS "completedAt" TIMESTAMP')
        )
        await conn.execute(
            text(
                'ALTER TABLE lists ADD COLUMN IF NOT EXISTS "isFinal"'
                " BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )


app.include_router(api_router, prefix=settings.API_STR)

origins = [
    "http://localhost:3000",  # Next.js local
    "http://127.0.0.1:3000",  # alternativa local
    "https://seu-frontend.com.br",  # (caso tenha um ambiente de produção)
]

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ou ["*"] para todos os domínios (não recomendado em produção)
    allow_credentials=True,
    allow_methods=["*"],  # permite todos os métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # permite todos os headers (incluindo Authorization)
)

# @app.get("health-check")
# def health_check():
#     return True


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)

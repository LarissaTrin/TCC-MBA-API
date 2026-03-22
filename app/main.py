import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.configs import settings
from app.core.limiter import limiter
from app.api.api import api_router
from app.db.conection import engine

IS_PRODUCTION = os.getenv("RENDER") is not None


app = FastAPI(
    title="TCC API",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

# ── Rate limiting ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Security headers ───────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)


@app.on_event("startup")
async def create_new_tables():
    async with engine.begin() as conn:
        await conn.run_sync(settings.DBBaseModel.metadata.create_all)
        await conn.execute(
            text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS "completedAt" TIMESTAMP')
        )
        await conn.execute(
            text(
                'ALTER TABLE lists ADD COLUMN IF NOT EXISTS "isFinal"'
                " BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        await conn.execute(
            text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS "sortOrder" INTEGER')
        )


app.include_router(api_router, prefix=settings.API_STR)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://trindade-to-do-list.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# @app.get("health-check")
# def health_check():
#     return True


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)

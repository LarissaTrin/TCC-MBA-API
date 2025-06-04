from fastapi import APIRouter

from app.api.routes import card_router, comments_router, project_router, user_router

api_router = APIRouter()

api_router.include_router(card_router.router, prefix="/cards", tags=["Cards"])
api_router.include_router(comments_router.router, prefix="/comments", tags=["Comments"])
api_router.include_router(project_router.router, prefix="/projects", tags=["Projects"])
api_router.include_router(user_router.router, prefix="/users", tags=["Users"])

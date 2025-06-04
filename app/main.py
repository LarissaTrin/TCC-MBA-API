from fastapi import FastAPI

from app.core.configs import settings
from app.api.api import api_router

app = FastAPI(title="TCC API")


app.include_router(api_router, prefix=settings.API_STR)


# @app.get("health-check")
# def health_check():
#     return True


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)

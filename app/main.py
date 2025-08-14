from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.configs import settings
from app.api.api import api_router

app = FastAPI(title="TCC API")


app.include_router(api_router, prefix=settings.API_STR)

origins = [
    "http://localhost:4200",  # Angular local
    "http://127.0.0.1:4200",  # alternativa local
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

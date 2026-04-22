from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assets import router as assets_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.llm import router as llm_router
from app.api.manuals import router as manuals_router
from app.api.reasoning import router as reasoning_router
from app.core.config import get_settings
from app.services.bootstrap import bootstrap_application


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(assets_router)
app.include_router(reasoning_router)
app.include_router(manuals_router)
app.include_router(chat_router)
app.include_router(llm_router)


@app.on_event("startup")
def on_startup() -> None:
    bootstrap_application()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }

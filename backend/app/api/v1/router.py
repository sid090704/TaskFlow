from fastapi import APIRouter

from app.routers import health,auth

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)
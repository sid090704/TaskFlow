from fastapi import APIRouter

from app.routers import health,auth,users,projects,tasks

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

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["Projects"],
)

api_router.include_router(
    tasks.router,
    prefix="/projects/{project_id}/tasks",
    tags=["Tasks"],
)
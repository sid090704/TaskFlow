from fastapi import APIRouter

from app.routers import health,auth,users,projects,tasks,comments,labels,attachments

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

api_router.include_router(
    comments.router,
    prefix="/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"],
)

api_router.include_router(
    labels.router,
    prefix="/projects/{project_id}",
    tags=["Labels"],
)

api_router.include_router(attachments.router)
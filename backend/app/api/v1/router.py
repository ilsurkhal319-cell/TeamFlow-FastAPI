from fastapi import APIRouter

from app.api.v1.endpoints import accessible_boards, auth, boards, collaboration, tasks, users, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(boards.router)
api_router.include_router(accessible_boards.router)
api_router.include_router(tasks.router)
api_router.include_router(collaboration.router)
api_router.include_router(users.router)

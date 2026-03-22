"""API v1 route registry."""

from fastapi import APIRouter

from app.api.v1.routes.applications import router as applications_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.candidates import router as candidates_router
from app.api.v1.routes.integrations import router as integrations_router
from app.api.v1.routes.jobs import router as jobs_router
from app.api.v1.routes.meta import router as meta_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(meta_router)
router.include_router(integrations_router)
router.include_router(jobs_router)
router.include_router(candidates_router)
router.include_router(applications_router)

__all__ = ["router"]

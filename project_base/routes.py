from fastapi import APIRouter

from pushes.routes import router as pushes_router

router = APIRouter()

router.include_router(pushes_router, prefix='/v1/pushes')

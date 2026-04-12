from fastapi import APIRouter

from app.api.routes import auth, design_versions, designs, exports, health, public_share
from app.realtime.ws_gateway import router as ws_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(designs.router)
api_router.include_router(design_versions.router)
api_router.include_router(exports.router)
api_router.include_router(public_share.router)
api_router.include_router(ws_router)

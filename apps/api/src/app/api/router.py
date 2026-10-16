from fastapi import APIRouter

from app.api.v1 import auth, files, health, items, realtime, users

v1 = APIRouter(prefix="/api/v1")
for module in (auth, users, items, files, realtime):
    v1.include_router(module.router)

# Probes live outside the versioned prefix.
root = APIRouter()
root.include_router(health.router)

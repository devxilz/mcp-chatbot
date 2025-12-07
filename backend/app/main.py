import os
from fastapi import FastAPI

from app.core.config import create_app
from app.core.settings import settings
from app.utils.model_loder import get_model

# Routers
from app.api.chat_routes import router as chat_router
from app.api.health import router as health_router
from app.api.profile_routes import router as profile_router
from app.api.memory_routes import router as memory_router

# Create the FastAPI app only once
app: FastAPI = create_app()

# Attach Routers (never inside create_app)
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(profile_router)
app.include_router(memory_router)


# STARTUP EVENT
@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.MEMORY_STORE_DIR, exist_ok=True)
    os.makedirs(settings.PROFILE_STORE_DIR, exist_ok=True)
    print("Directories ensured.")
    print("Backend starting...")
    get_model()             # Load your ML model
    print(f"App Name: {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")

# SHUTDOWN EVENT
@app.on_event("shutdown")
async def shutdown_event():
    print("Backend shutting down...")

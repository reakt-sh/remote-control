from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from managers.train_manager import TrainManager
from managers.control_manager import ControlManager
from managers.log_manager import logger

from config import settings

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
logger.debug("Initializing managers...")
train_manager = TrainManager()
control_manager = ControlManager()

@app.on_event("startup")
async def startup():
    logger.info("Starting up the server...")
    pass

@app.on_event("shutdown")
async def shutdown():
    """Clean up connections"""
    await train_manager.disconnect_all()
    await control_manager.disconnect_all()
    logger.info("Shutting down the server...")
    pass

# Include routers
from endpoints import video, commands
app.include_router(video.router)
app.include_router(commands.router)
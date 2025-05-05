from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from managers.train_manager import TrainManager
from managers.control_manager import ControlManager
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
train_manager = TrainManager()
control_manager = ControlManager()

@app.on_event("startup")
async def startup():
    """Initialize WebSocket relay tasks"""
    pass

@app.on_event("shutdown")
async def shutdown():
    """Clean up connections"""
    await train_manager.disconnect_all()
    await control_manager.disconnect_all()

# Include routers
from endpoints import video, commands
app.include_router(video.router)
app.include_router(commands.router)
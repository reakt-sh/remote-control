from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from managers.train_manager import TrainManager
from managers.remote_control_manager import RemoteControlManager
from managers.log_manager import logger
from endpoints import remote_control_gateway
from endpoints import train_gateway

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
remote_control_manager = RemoteControlManager()

@app.on_event("startup")
async def startup():
    logger.info("Starting up the server...")
    pass

@app.on_event("shutdown")
async def shutdown():
    await train_manager.disconnect_all()
    await remote_control_manager.disconnect_all()
    logger.info("Shutting down the server...")
    pass

# Include routers
app.include_router(train_gateway.router)
app.include_router(remote_control_gateway.router)
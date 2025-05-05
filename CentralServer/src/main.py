from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from server_controller import ServerController
from utils.app_logger import logger
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

serverController = ServerController()

@app.on_event("startup")
async def startup():
    logger.info("Starting up the server...")
    serverController.start_server()
    pass

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down the server...")
    await serverController.stop_server()
    pass

# Include routers
app.include_router(train_gateway.router)
app.include_router(remote_control_gateway.router)
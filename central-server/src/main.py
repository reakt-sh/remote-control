import threading
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.server_controller import ServerController
from src.utils.app_logger import logger
from src.endpoints import remote_control_gateway
from src.endpoints import train_gateway
from src.config import settings
from src.quic_server import run_quic_server

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
    logger.info("Starting up FastAPI() server...")
    serverController.start_server()

    # Start QUIC server in a background thread
    threading.Thread(target=lambda: asyncio.run(run_quic_server()), daemon=True).start()



@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down FastAPI server...")
    await serverController.stop_server()
    pass

# Include routers
app.include_router(train_gateway.router)
app.include_router(remote_control_gateway.router)
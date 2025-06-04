import uvicorn
import threading
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from server_controller import ServerController
from utils.app_logger import logger
from endpoints import remote_control_gateway
from endpoints import train_gateway
from config import settings
from quic_server import run_quic_server
from globals import *

serverController = ServerController()

@asynccontextmanager
async def lifespan(app):
    logger.info(f"FastAPI server running at http://{HOST}:{FAST_API_PORT}")
    serverController.start_server()
    # Start QUIC server in a background thread
    quic_thread = threading.Thread(target=lambda: asyncio.run(run_quic_server()), daemon=True)
    quic_thread.start()
    yield
    logger.info("Shutting down FastAPI server...")
    quic_thread.join(timeout=1)
    await serverController.stop_server()

app = FastAPI(lifespan=lifespan)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(train_gateway.router)
app.include_router(remote_control_gateway.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=FAST_API_PORT,
        reload=True
    )
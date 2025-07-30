import uvicorn
import threading
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from server_controller import ServerController
from utils.app_logger import logger
from utils.iperf3_process import Iperf3Process
from endpoints import remote_control_gateway
from endpoints import train_gateway
from config import settings
from quic_server import run_quic_server
from mqtt_bridge import run_mqtt_bridge
from globals import *

serverController = ServerController()

@asynccontextmanager
async def lifespan(app):
    logger.info(f"FastAPI server running at http://{HOST}:{FAST_API_PORT}")
    serverController.start_server()
    
    # Start QUIC server in a background thread
    quic_thread = threading.Thread(target=lambda: asyncio.run(run_quic_server()), daemon=True)
    quic_thread.start()
    
    # Start MQTT bridge in a background thread
    mqtt_thread = threading.Thread(target=run_mqtt_bridge, daemon=True)
    mqtt_thread.start()

    # Start iperf3 server process
    iperf3_process = Iperf3Process()
    iperf3_process.create_process()
    
    yield
    
    logger.info("Shutting down FastAPI server...")
    quic_thread.join(timeout=1)
    mqtt_thread.join(timeout=1)
    await serverController.stop_server()
    iperf3_process.destroy_process()

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

config = get_client_config()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=FAST_API_PORT,
        reload=True,
        ssl_keyfile=config.key_file,
        ssl_certfile=config.cert_file,
    )
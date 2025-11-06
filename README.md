# Remote Control System

Welcome to the **Remote Control System** by reakt-sh, a robust solution designed to manage and control train operations remotely. This repository contains three core modules: `train-client`, `central-server`, and `web-client`. Each module serves a distinct purpose in enabling seamless communication, control, and monitoring of train systems. Below, you'll find a detailed overview of the features for each module.

## Table of Contents
- [Overview](#overview)
- [Languages and Frameworks](#languages-and-frameworks)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Overview
The Remote Control System is designed to facilitate real-time monitoring, control, and data exchange for train operations. It comprises:
- **Train Client**: Runs on train hardware to manage onboard operations and communicate with the central server.
- **Central Server**: Acts as the backbone, handling data aggregation, command processing, and communication between trains and web clients.
- **Web Client**: Provides a user-friendly interface for operators to monitor and control train operations remotely.

This system ensures reliability, scalability, and security for modern railway management.

## Languages and Frameworks

The Remote Control System is built using a modern, heterogeneous technology stack optimized for real-time communication and performance across distributed components.

### Train Client
The train client is developed in **Python 3**, leveraging **PyQt5** for the graphical user interface and system event handling. Video processing and encoding are handled through **OpenCV**, **PyAV**, and **FFmpeg**, enabling efficient H.264 video stream encoding from onboard cameras. The client supports multiple communication protocols including **QUIC** (via `aioquic` library), **WebSocket** (`websockets`), and **MQTT** (`paho-mqtt`) for reliable, low-latency data transmission under varying network conditions. **NumPy** is utilized for numerical computations related to sensor data processing.

### Central Server
The central server is implemented in **Python 3** using the **FastAPI** framework, which provides high-performance asynchronous HTTP and WebSocket capabilities through **Uvicorn** ASGI server. The server architecture supports multiple concurrent communication protocols: **WebRTC** (implemented via `aiortc` and `aioice` libraries) for peer-to-peer video streaming, **QUIC** protocol for low-latency transport, and **MQTT** (using `paho-mqtt`) for message brokering. The server integrates **NanoMQ** (version 0.19.0) as a lightweight MQTT broker, deployed via Docker containers for easy scalability. Video processing capabilities are provided through **OpenCV** and **NumPy**, while **Loguru** handles structured logging. For production deployment, the server utilizes **Gunicorn** with **uvloop** for enhanced event loop performance on Linux systems.

### Web Client
The web client is a modern single-page application built with **Vue.js 3** and managed through **Vue CLI**. The application uses **Pinia** for state management and **Vue Router** for client-side routing. Real-time communication is achieved through **WebSocket** connections and **MQTT** (via `paho-mqtt` browser library). Video streaming utilizes the **H.264 Live Player** library for efficient decoding and rendering of H.264 video streams directly in the browser. The UI is enhanced with **Font Awesome** icons, and **Axios** handles HTTP requests to the central server. The client employs **Dexie.js** for IndexedDB-based local storage of recorded sessions and telemetry data. Network performance monitoring is integrated using the **Fast Speedtest API**. The build process uses **Babel** for JavaScript transpilation and **ESLint** for code quality enforcement, ensuring cross-browser compatibility and maintainable code.

This multi-layered architecture ensures optimal performance, real-time responsiveness, and maintainability while supporting diverse deployment scenarios from embedded systems to web browsers.

## Usage
1. **Train Client**:
   - Deploy on train hardware and configure to connect to the central server.
   - Monitor logs for telemetry data and command execution status.

2. **Central Server**:
   - Server prepared with WebSocket, QUIC and WebTransport Connection
   - Use API endpoints to connect with clients.

3. **Web Client**:
   - Open the web interface in a browser (e.g., `http://localhost:8080`).
   - Watch video and telemetry data to monitor and control trains.

## Contributing
We welcome contributions to improve the Remote Control System! To contribute:
1. Create a feature branch (`git checkout -b your-feature`).
2. Commit your changes (`git commit -m "Add your feature"`).
3. Push to the branch (`git push origin your-feature`).
4. Open a pull request to main branch on GitHub.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

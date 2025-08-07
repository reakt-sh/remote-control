# Remote Control System

Welcome to the **Remote Control System** by reakt-sh, a robust solution designed to manage and control train operations remotely. This repository contains three core modules: `train-client`, `central-server`, and `web-client`. Each module serves a distinct purpose in enabling seamless communication, control, and monitoring of train systems. Below, you'll find a detailed overview of the features for each module.

## Table of Contents
- [Overview](#overview)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Overview
The Remote Control System is designed to facilitate real-time monitoring, control, and data exchange for train operations. It comprises:
- **Train Client**: Runs on train hardware to manage onboard operations and communicate with the central server.
- **Central Server**: Acts as the backbone, handling data aggregation, command processing, and communication between trains and web clients.
- **Web Client**: Provides a user-friendly interface for operators to monitor and control train operations remotely.

This system ensures reliability, scalability, and security for modern railway management.

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

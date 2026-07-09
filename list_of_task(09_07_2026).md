- ### Performance Analysis
	- Improve end-to-end latency measurement by integrating NTP-based time synchronization for more accurate calculations.
	- Migrate analysis data storage from the browser client to the server to ensure data persistence and prevent loss after test sessions.
- ### User Interfacence
	- Refine the UI by removing unnecessary or distracting components.
	- Prevent users from changing the train's direction while it is moving in one direction.
	- Enhance the overall user experience by improving usability
- ### Distributed System Architecture
	- Design and implement support for running the VideoStreamer module on a separate device while keeping TrainClient responsible for processing the received video data.
	- Establish communication between VideoStreamer and TrainClient over the local network.
- ### Long-Duration Testing
	- Conduct long-duration testing on Labor (minimum of one hour per session) to evaluate system stability, reliability, and performance under continuous operation.
	- Monitor system behavior during extended runs, identify issues such as memory leaks, performance, or communication failures, and note findings for further improvements.
  ### Others
	- Integrate the GPS sensor, specially for longer tests
	- React to the fact that if the latency is increased more then 200 ms, need to think about safety precaution
		- reduce the speed
		- alert the remote control operator in the interface
	- Integrate second Camera, so that remote operator can drive both direction. (Network Camera)

  ### Hardware requirement
  	- 5G router (Done)
	- 20000 mAh Battery for Router (Done)
	- RPi5 + Battery for TrainClient + Driver Control (Done)
	- RPi3 + PiCam 1 for VideoStream (Front) (Done)
	- RPi5 + PiCam 2 for VideoStream (Back) (We need to buy it)


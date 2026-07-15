## Performance Analysis and Evaluation
- Improve end-to-end latency measurement accuracy by integrating NTP-based time synchronization.
- Migrate analysis data storage from the browser client to the server to ensure data persistence and prevent data loss after test sessions.

## User Interface (PRIORITY HIGH for LiveDemo)
- Implement a second video canvas to support the display of the second video stream.
- Design 3–4 realistic UI concepts for the remote control system and prepare a presentation for discussion with the working group during the Tea Meeting on 20th July.
- Refine and improve the UI design based on feedback from the working group.
- Implement safety restrictions to prevent users from changing the train direction while the train is moving.
- Improve overall user experience by enhancing usability, accessibility, and interaction flow.

## Distributed Camera Sensor System (PRIORITY HIGH for LiveDemo)
- Design and implement support for running the VideoStreamer module on a separate device while keeping TrainClient responsible for receiving and processing video streams.
  - Modify the video transmission pipeline to support external camera sources instead of direct camera access. [DONE]
  - Extend the video header information to include camera identification (front/rear) so that the receiver can correctly separate and process multiple streams.
  - Update the frame parser on the receiving side to support the new video stream.

- Establish communication between VideoStreamer and TrainClient over the local network.
  - Configure two Raspberry Pis as RTSP stream providers using GStreamer or MediaMTX for development purposes. (The setup may later be replaced with dedicated IP cameras.) [DONE]
  - Extend TrainClient to receive and process two RTSP streams simultaneously (front and rear cameras). [DONE]
- Research IP camera specifications, including viewing angle, focal length, resolution, and other relevant parameters, to select a suitable camera model.


## Long-Duration Testing
- Conduct long-duration tests in the laboratory (minimum one hour per session) to evaluate system stability, reliability, and performance during continuous operation.
- Monitor system behavior during extended runs and identify potential issues, including:
  - Memory leaks
  - Performance degradation
  - Communication failures
  - Other stability-related problems
- Document test results and findings to guide future improvements.

## Additional Tasks
- Integrate GPS sensor support, especially for long-duration testing scenarios.
- Define safety mechanisms for situations where latency exceeds 200 ms:
  - Automatically reduce train speed.
  - Provide latency warnings/alerts to the remote control operator through the user interface.

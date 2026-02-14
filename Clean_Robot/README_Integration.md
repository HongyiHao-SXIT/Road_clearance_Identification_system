ESP32 integration notes

Purpose
- Show how the ESP32CAM and ESP32S3 Motor Controller can be integrated with the Flask server in this project.

1) ESP32CAM (networked unit)
- The `ESP32CAM_Controller.ino` sketch now includes a best-effort HTTP POST to `/api/robot/status_update`.
- Set `SERVER_BASE` and `ROBOT_DEVICE_ID` at the top of the sketch to point to your server and device id.
- Because many camera boards do not have GPS, the sketch currently posts `lat=0` and `lng=0`. If you have a GPS module or the motor controller can provide pose over serial, forward that into these fields.
- Example minimal JSON payload posted:
  {
    "device_id": "ESP32CAM-001",
    "lat": 0.0,
    "lng": 0.0,
    "battery": 87,
    "status": "ONLINE"
  }

2) ESP32S3 Motor Controller (low-level controller)
- The `ESP32S3_MotorController.ino` sketch currently uses serial for command input and prints sensor JSON to serial.
- Options to integrate with the server:
  - Option A (recommended): Keep motor controller as local, connect it to a networked board (ESP32CAM or a separate ESP32-WROOM) by UART. The networked board receives sensor data from motor controller and posts to the server via HTTP, and forwards remote commands back to the motor controller over serial.
  - Option B: Add WiFi + HTTPClient into the motor controller sketch (if your board has WiFi) and implement POST/GET to `/api/robot/status_update` and poll `/api/robot/list` or a command endpoint. That requires adding WiFi credentials and HTTPClient usage similar to the camera sketch.

3) Example flow (Option A)
- Motor controller prints sensor JSON to serial every 500ms.
- ESP32CAM reads serial, parses JSON, extracts battery/position, and POSTs to `/api/robot/status_update`.
- Server may respond with `next_command` or `target`; ESP32CAM can forward these to motor controller via serial as JSON commands.

4) Security
- Currently the Flask server's robot endpoints are unprotected (auth removed earlier). For production you should secure these endpoints (API key, TLS, mutual auth, or simple signed tokens).

5) Flash & test
- Edit `SERVER_BASE` in `ESP32CAM_Controller.ino` to point to your server IP/port.
- Edit `ROBOT_DEVICE_ID` to match the record in the server DB or register the device using `/api/robot/register` first.

6) Troubleshooting
- If status posts fail, monitor Serial console for errors and ensure the server is reachable from the robot network and CORS/proxies permit the POST.


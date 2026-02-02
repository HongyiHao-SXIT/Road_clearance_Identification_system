/*
 * ESP32CAM Controller for Robot Control System
 * 机器人远程监控摄像头代码
 * 使用ESP32CAM实现视频流传输、WebSocket通信和摄像头控制
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ESPAsyncWebServer.h>
#include <AsyncWebSocket.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include <FS.h>
#include <SPIFFS.h>

// WiFi配置
const char* ssid = "YourWiFiSSID";
const char* password = "YourWiFiPassword";

// 服务器端口
#define HTTP_SERVER_PORT 8080
#define WEBSOCKET_PORT 81

// 摄像头引脚定义（根据实际模块调整）
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// 电池电压检测引脚
#define BATTERY_PIN 33

// Web服务器和WebSocket服务器
AsyncWebServer server(HTTP_SERVER_PORT);
AsyncWebSocket ws("/");

// 摄像头状态
struct CameraStatus {
  bool streaming = true;
  String resolution = "640x480";
  int frameRate = 25;
  int battery = 100;
  bool connected = false;
} cameraStatus;

// 视频流客户端计数
int streamClients = 0;

// JSON文档大小
#define JSON_DOC_SIZE 1024

// 初始化摄像头
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  
  // 设置摄像头像素格式
  config.pixel_format = PIXFORMAT_JPEG;
  
  // 设置分辨率
  if (cameraStatus.resolution == "640x480") {
    config.frame_size = FRAMESIZE_VGA;
  } else if (cameraStatus.resolution == "320x240") {
    config.frame_size = FRAMESIZE_QVGA;
  } else if (cameraStatus.resolution == "1280x720") {
    config.frame_size = FRAMESIZE_SVGA;
  } else {
    config.frame_size = FRAMESIZE_VGA;
  }
  
  config.jpeg_quality = 12;
  config.fb_count = 2;
  
  // 初始化摄像头
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return false;
  }
  
  Serial.println("Camera initialized successfully");
  return true;
}

// 读取电池电量
int readBatteryLevel() {
  int batteryValue = analogRead(BATTERY_PIN);
  // 转换为0-100%电量
  // 注意：实际转换系数需要根据硬件电路调整
  int batteryPercent = map(batteryValue, 1500, 2400, 0, 100);
  return constrain(batteryPercent, 0, 100);
}

// 发送JSON消息给所有WebSocket客户端
void sendWebSocketMessage(const char* message) {
  ws.textAll(message);
}

// 发送摄像头状态
void sendCameraStatus() {
  StaticJsonDocument<JSON_DOC_SIZE> doc;
  
  doc["type"] = "status";
  JsonObject data = doc.createNestedObject("data");
  data["connected"] = cameraStatus.connected;
  data["streaming"] = cameraStatus.streaming;
  data["resolution"] = cameraStatus.resolution;
  data["frameRate"] = cameraStatus.frameRate;
  data["battery"] = cameraStatus.battery;
  data["streamClients"] = streamClients;
  
  char buffer[JSON_DOC_SIZE];
  serializeJson(doc, buffer);
  sendWebSocketMessage(buffer);
}

// 处理WebSocket事件
void onWebSocketEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
                     AwsEventType type, void *arg, uint8_t *data, size_t len) {
  
  switch (type) {
    case WS_EVT_CONNECT: {
      Serial.printf("WebSocket client #%u connected from %s\n", 
                   client->id(), client->remoteIP().toString().c_str());
      cameraStatus.connected = true;
      // 发送初始状态
      sendCameraStatus();
      break;
    }
    case WS_EVT_DISCONNECT: {
      Serial.printf("WebSocket client #%u disconnected\n", client->id());
      // 检查是否还有其他连接
      if (server->count() == 0) {
        cameraStatus.connected = false;
      }
      break;
    }
    case WS_EVT_DATA: {
      AwsFrameInfo *info = (AwsFrameInfo*)arg;
      if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
        // 处理接收到的命令
        data[len] = 0;
        String message = (char*)data;
        
        Serial.printf("Received command: %s\n", message.c_str());
        
        // 解析JSON命令
        StaticJsonDocument<JSON_DOC_SIZE> doc;
        DeserializationError error = deserializeJson(doc, message);
        
        if (error) {
          Serial.printf("JSON parse error: %s\n", error.c_str());
          return;
        }
        
        String commandType = doc["type"];
        
        if (commandType == "status") {
          // 请求状态
          sendCameraStatus();
        } else if (commandType == "stream") {
          // 流媒体控制
          String action = doc["action"];
          if (action == "start") {
            cameraStatus.streaming = true;
            Serial.println("Streaming started");
          } else if (action == "stop") {
            cameraStatus.streaming = false;
            Serial.println("Streaming stopped");
          }
          sendCameraStatus();
        } else if (commandType == "config") {
          // 配置命令
          JsonObject config = doc["data"];
          
          if (config.containsKey("resolution")) {
            String resolution = config["resolution"];
            cameraStatus.resolution = resolution;
            Serial.printf("Resolution set to: %s\n", resolution.c_str());
            // 重启摄像头以应用新分辨率
            esp_camera_deinit();
            initCamera();
          }
          
          if (config.containsKey("frameRate")) {
            int frameRate = config["frameRate"];
            cameraStatus.frameRate = constrain(frameRate, 1, 60);
            Serial.printf("Frame rate set to: %d FPS\n", cameraStatus.frameRate);
          }
          
          sendCameraStatus();
        }
      }
      break;
    }
    default:
      break;
  }
}

// JPEG视频流处理
void handleStreamRequest(AsyncWebServerRequest *request) {
  Serial.println("Stream request received");
  
  streamClients++;
  
  // 设置响应头
  request->sendContent("HTTP/1.1 200 OK\n");
  request->sendContent("Content-Type: multipart/x-mixed-replace; boundary=frame\n");
  request->sendContent("\n");
  
  // 持续发送视频帧
  while (cameraStatus.streaming && streamClients > 0) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      // 发送帧边界
      request->sendContent("--frame\n");
      // 发送帧头
      request->sendContent("Content-Type: image/jpeg\n");
      request->sendContent(String("Content-Length: ") + String(fb->len) + "\n");
      request->sendContent("\n");
      // 发送帧数据
      request->sendContent((const char *)fb->buf, fb->len);
      request->sendContent("\n");
      
      // 释放帧缓冲区
      esp_camera_fb_return(fb);
      
      // 根据帧率控制发送间隔
      delay(1000 / cameraStatus.frameRate);
    }
  }
  
  streamClients--;
  Serial.println("Stream client disconnected");
}

// 根路径处理
void handleRootRequest(AsyncWebServerRequest *request) {
  request->send(200, "text/plain", "ESP32 Camera Server\nStream URL: /stream\nWebSocket URL: ws://" + WiFi.localIP().toString() + ":" + String(WEBSOCKET_PORT));
}

// 读取WiFi信号强度
int getWifiSignalStrength() {
  return WiFi.RSSI();
}

// 初始化WiFi
void initWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Connecting to WiFi..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
  
  Serial.println();
  Serial.print("WiFi connected. IP address: ");
  Serial.println(WiFi.localIP());
  
  // 设置mDNS
  if (!MDNS.begin("esp32-camera")) {
    Serial.println("Error setting up MDNS responder!");
  } else {
    Serial.println("mDNS responder started");
  }
}

// 初始化服务器
void initServer() {
  // 注册WebSocket事件处理
  ws.onEvent(onWebSocketEvent);
  server.addHandler(&ws);
  
  // 注册HTTP路由
  server.on("/", HTTP_GET, handleRootRequest);
  server.on("/stream", HTTP_GET, handleStreamRequest);
  
  // 启动服务器
  server.begin();
  Serial.printf("HTTP server started on port %d\n", HTTP_SERVER_PORT);
  Serial.printf("WebSocket server started on port %d\n", WEBSOCKET_PORT);
}

// 初始化OTA更新
void initOTA() {
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {
      type = "filesystem";
    }
    Serial.println("OTA Update started: " + type);
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("OTA Update finished");
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("OTA Progress: %u%%\r", (progress / (total / 100)));
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA Error: %u\n", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("OTA Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("OTA Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("OTA Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("OTA Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("OTA End Failed");
    }
  });
  
  ArduinoOTA.begin();
  Serial.println("OTA Update initialized");
}

// 初始化
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32CAM Controller initialized");
  
  // 初始化文件系统
  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS Mount Failed");
    return;
  }
  
  // 初始化WiFi
  initWiFi();
  
  // 初始化摄像头
  if (!initCamera()) {
    return;
  }
  
  // 初始化服务器
  initServer();
  
  // 初始化OTA
  initOTA();
  
  // 初始化电池检测引脚
  pinMode(BATTERY_PIN, INPUT);
  
  Serial.println("System ready!");
  Serial.printf("Stream URL: http://%s:%d/stream\n", WiFi.localIP().toString().c_str(), HTTP_SERVER_PORT);
  Serial.printf("WebSocket URL: ws://%s:%d\n", WiFi.localIP().toString().c_str(), WEBSOCKET_PORT);
}

// 主循环
void loop() {
  // 处理OTA更新
  ArduinoOTA.handle();
  
  // 处理WebSocket消息
  ws.cleanupClients();
  
  // 更新电池电量（每1秒）
  static unsigned long lastBatteryUpdate = 0;
  if (millis() - lastBatteryUpdate > 1000) {
    cameraStatus.battery = readBatteryLevel();
    lastBatteryUpdate = millis();
  }
  
  // 发送状态更新（每5秒）
  static unsigned long lastStatusUpdate = 0;
  if (millis() - lastStatusUpdate > 5000) {
    sendCameraStatus();
    lastStatusUpdate = millis();
  }
  
  // 打印调试信息（每10秒）
  static unsigned long lastDebugPrint = 0;
  if (millis() - lastDebugPrint > 10000) {
    Serial.printf("Status: Streaming=%d, Resolution=%s, FPS=%d, Battery=%d%%, Clients=%d, WiFi=%ddBm\n", 
                 cameraStatus.streaming, 
                 cameraStatus.resolution.c_str(), 
                 cameraStatus.frameRate, 
                 cameraStatus.battery, 
                 streamClients, 
                 getWifiSignalStrength());
    lastDebugPrint = millis();
  }
  
  delay(10);
}
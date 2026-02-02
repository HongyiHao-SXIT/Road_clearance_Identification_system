/*
 * ESP32S3 Motor Controller for Robot Control System
 * 机器人运动控制主控代码
 * 使用ESP32S3实现4轮底盘控制、传感器数据采集和串口通信
 */

#include <Arduino.h>
#include <HardwareSerial.h>

// 串口配置
#define SERIAL_BAUD_RATE 115200

// 电机控制引脚
#define LEFT_MOTOR_IN1 2
#define LEFT_MOTOR_IN2 3
#define LEFT_MOTOR_EN 4
#define RIGHT_MOTOR_IN1 5
#define RIGHT_MOTOR_IN2 6
#define RIGHT_MOTOR_EN 7

// 超声传感器引脚配置（障碍物检测）
#define OBSTACLE_FRONT_TRIG 8
#define OBSTACLE_FRONT_ECHO 9
#define OBSTACLE_REAR_TRIG 10
#define OBSTACLE_REAR_ECHO 11
#define OBSTACLE_RIGHT_TRIG 12
#define OBSTACLE_RIGHT_ECHO 13

// 超声传感器引脚配置（贴边行驶）
#define EDGE_FRONT_TRIG 14
#define EDGE_FRONT_ECHO 15
#define EDGE_MIDDLE_TRIG 16
#define EDGE_MIDDLE_ECHO 17
#define EDGE_REAR_TRIG 18
#define EDGE_REAR_ECHO 19

// 电池电压检测引脚
#define BATTERY_PIN 20

// 超声传感器测量最大距离（cm）
#define MAX_DISTANCE 200

// 电机速度范围（0-255）
#define MOTOR_MAX_SPEED 255

// 控制模式
enum ControlMode {
  MODE_MANUAL,      // 手动控制模式
  MODE_EDGE_FOLLOW  // 贴边行驶模式
};

// 障碍物阈值默认值
struct ObstacleThresholds {
  int front = 30;
  int rear = 30;
  int right = 30;
} obstacleThresholds;

// 贴边行驶配置
struct EdgeConfig {
  int targetDistance = 20;  // 目标贴边距离（cm）
  int threshold = 5;        // 贴边距离阈值（cm）
} edgeConfig;

// 当前控制模式
ControlMode currentMode = MODE_MANUAL;

// 电机速度
int leftMotorSpeed = 0;
int rightMotorSpeed = 0;

// 传感器数据
struct SensorData {
  // 障碍物检测传感器
  int obstacleFront = 0;
  int obstacleRear = 0;
  int obstacleRight = 0;
  
  // 贴边控制传感器
  int edgeFront = 0;
  int edgeMiddle = 0;
  int edgeRear = 0;
  
  // 电池电量
  int battery = 0;
} sensorData;

// 解析JSON命令
struct Command {
  String type;
  int leftSpeed;
  int rightSpeed;
  ControlMode mode;
  ObstacleThresholds obstacleThresholds;
  EdgeConfig edgeConfig;
} currentCommand;

// 初始化超声传感器
void initUltrasonicSensor(int trigPin, int echoPin) {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW);
}

// 读取超声传感器距离（cm）
int readUltrasonicDistance(int trigPin, int echoPin) {
  // 发送10us触发脉冲
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // 计算距离
  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;
  
  // 限制距离范围
  if (distance > MAX_DISTANCE) {
    distance = MAX_DISTANCE;
  }
  if (distance < 0) {
    distance = 0;
  }
  
  return distance;
}

// 初始化电机控制引脚
void initMotors() {
  pinMode(LEFT_MOTOR_IN1, OUTPUT);
  pinMode(LEFT_MOTOR_IN2, OUTPUT);
  pinMode(LEFT_MOTOR_EN, OUTPUT);
  pinMode(RIGHT_MOTOR_IN1, OUTPUT);
  pinMode(RIGHT_MOTOR_IN2, OUTPUT);
  pinMode(RIGHT_MOTOR_EN, OUTPUT);
  
  // 初始化电机为停止状态
  digitalWrite(LEFT_MOTOR_IN1, LOW);
  digitalWrite(LEFT_MOTOR_IN2, LOW);
  analogWrite(LEFT_MOTOR_EN, 0);
  digitalWrite(RIGHT_MOTOR_IN1, LOW);
  digitalWrite(RIGHT_MOTOR_IN2, LOW);
  analogWrite(RIGHT_MOTOR_EN, 0);
}

// 设置电机速度和方向
void setMotorSpeed(int motor, int speed) {
  if (motor == 0) {
    // 左电机
    if (speed > 0) {
      // 正转
      digitalWrite(LEFT_MOTOR_IN1, HIGH);
      digitalWrite(LEFT_MOTOR_IN2, LOW);
      analogWrite(LEFT_MOTOR_EN, speed);
    } else if (speed < 0) {
      // 反转
      digitalWrite(LEFT_MOTOR_IN1, LOW);
      digitalWrite(LEFT_MOTOR_IN2, HIGH);
      analogWrite(LEFT_MOTOR_EN, -speed);
    } else {
      // 停止
      digitalWrite(LEFT_MOTOR_IN1, LOW);
      digitalWrite(LEFT_MOTOR_IN2, LOW);
      analogWrite(LEFT_MOTOR_EN, 0);
    }
  } else {
    // 右电机
    if (speed > 0) {
      // 正转
      digitalWrite(RIGHT_MOTOR_IN1, HIGH);
      digitalWrite(RIGHT_MOTOR_IN2, LOW);
      analogWrite(RIGHT_MOTOR_EN, speed);
    } else if (speed < 0) {
      // 反转
      digitalWrite(RIGHT_MOTOR_IN1, LOW);
      digitalWrite(RIGHT_MOTOR_IN2, HIGH);
      analogWrite(RIGHT_MOTOR_EN, -speed);
    } else {
      // 停止
      digitalWrite(RIGHT_MOTOR_IN1, LOW);
      digitalWrite(RIGHT_MOTOR_IN2, LOW);
      analogWrite(RIGHT_MOTOR_EN, 0);
    }
  }
}

// 读取电池电量
int readBatteryLevel() {
  int batteryValue = analogRead(BATTERY_PIN);
  // 转换为0-100%电量
  int batteryPercent = map(batteryValue, 0, 4095, 0, 100);
  return constrain(batteryPercent, 0, 100);
}

// 检测障碍物
bool detectObstacles() {
  bool obstacleDetected = false;
  
  if (sensorData.obstacleFront < obstacleThresholds.front) {
    obstacleDetected = true;
    Serial.println("[Interrupt] Obstacle detected in front!");
  }
  
  if (sensorData.obstacleRear < obstacleThresholds.rear) {
    obstacleDetected = true;
    Serial.println("[Interrupt] Obstacle detected in rear!");
  }
  
  if (sensorData.obstacleRight < obstacleThresholds.right) {
    obstacleDetected = true;
    Serial.println("[Interrupt] Obstacle detected on right!");
  }
  
  return obstacleDetected;
}

// 贴边行驶控制
void edgeFollowingControl() {
  // 计算左侧平均距离
  int leftAverage = (sensorData.edgeFront + sensorData.edgeMiddle + sensorData.edgeRear) / 3;
  int error = leftAverage - edgeConfig.targetDistance;
  
  // PID控制参数（简化版，仅使用P控制）
  float kp = 5.0;
  int correction = (int)(error * kp);
  
  // 基础速度
  int baseSpeed = 150;
  
  // 计算左右轮速度
  int leftSpeed = baseSpeed - correction;
  int rightSpeed = baseSpeed + correction;
  
  // 限制速度范围
  leftSpeed = constrain(leftSpeed, 0, MOTOR_MAX_SPEED);
  rightSpeed = constrain(rightSpeed, 0, MOTOR_MAX_SPEED);
  
  // 设置电机速度
  setMotorSpeed(0, leftSpeed);
  setMotorSpeed(1, rightSpeed);
}

// 解析JSON命令
void parseCommand(String jsonString) {
  // 简单JSON解析，实际项目中建议使用ArduinoJson库
  
  if (jsonString.indexOf("motor") > 0) {
    // 电机控制命令
    int leftSpeedIndex = jsonString.indexOf("leftSpeed");
    int rightSpeedIndex = jsonString.indexOf("rightSpeed");
    
    if (leftSpeedIndex > 0 && rightSpeedIndex > 0) {
      leftMotorSpeed = jsonString.substring(leftSpeedIndex + 10).toInt();
      rightMotorSpeed = jsonString.substring(rightSpeedIndex + 11).toInt();
      
      // 设置电机速度
      setMotorSpeed(0, leftMotorSpeed);
      setMotorSpeed(1, rightMotorSpeed);
      
      // 切换到手动模式
      currentMode = MODE_MANUAL;
      
      Serial.print("[Command] Motor speed set to L:");
      Serial.print(leftMotorSpeed);
      Serial.print(", R:");
      Serial.println(rightMotorSpeed);
    }
  }
  
  if (jsonString.indexOf("mode") > 0) {
    // 模式切换命令
    if (jsonString.indexOf("edge_following") > 0) {
      currentMode = MODE_EDGE_FOLLOW;
      Serial.println("[Command] Mode switched to Edge Following");
    } else {
      currentMode = MODE_MANUAL;
      Serial.println("[Command] Mode switched to Manual");
    }
  }
  
  if (jsonString.indexOf("config") > 0) {
    // 配置命令
    if (jsonString.indexOf("obstacleThresholds") > 0) {
      // 更新障碍物阈值
      int frontIndex = jsonString.indexOf("front");
      int rearIndex = jsonString.indexOf("rear");
      int rightIndex = jsonString.indexOf("right");
      
      if (frontIndex > 0) {
        obstacleThresholds.front = jsonString.substring(frontIndex + 6).toInt();
      }
      if (rearIndex > 0) {
        obstacleThresholds.rear = jsonString.substring(rearIndex + 5).toInt();
      }
      if (rightIndex > 0) {
        obstacleThresholds.right = jsonString.substring(rightIndex + 6).toInt();
      }
      
      Serial.println("[Command] Obstacle thresholds updated");
    }
    
    if (jsonString.indexOf("edgeDistance") > 0) {
      // 更新贴边距离
      int distanceIndex = jsonString.indexOf("edgeDistance");
      if (distanceIndex > 0) {
        edgeConfig.targetDistance = jsonString.substring(distanceIndex + 13).toInt();
        Serial.print("[Command] Edge distance updated to:");
        Serial.println(edgeConfig.targetDistance);
      }
    }
    
    if (jsonString.indexOf("edgeThreshold") > 0) {
      // 更新贴边阈值
      int thresholdIndex = jsonString.indexOf("edgeThreshold");
      if (thresholdIndex > 0) {
        edgeConfig.threshold = jsonString.substring(thresholdIndex + 14).toInt();
        Serial.print("[Command] Edge threshold updated to:");
        Serial.println(edgeConfig.threshold);
      }
    }
  }
}

// 发送传感器数据
void sendSensorData() {
  String jsonData = "{\"type\":\"sensor\",\"data\":{";
  
  // 障碍物检测传感器数据
  jsonData += "\"obstacles\":{";
  jsonData += "\"front\":" + String(sensorData.obstacleFront) + ",";
  jsonData += "\"rear\":" + String(sensorData.obstacleRear) + ",";
  jsonData += "\"right\":" + String(sensorData.obstacleRight);
  jsonData += "},";
  
  // 贴边传感器数据
  jsonData += "\"leftSide\":{";
  jsonData += "\"sensor1\":" + String(sensorData.edgeFront) + ",";
  jsonData += "\"sensor2\":" + String(sensorData.edgeMiddle) + ",";
  jsonData += "\"sensor3\":" + String(sensorData.edgeRear);
  jsonData += "},";
  
  // 电池电量
  jsonData += "\"battery\":" + String(sensorData.battery);
  
  jsonData += "}}";
  
  Serial.println(jsonData);
}

// 初始化
void setup() {
  // 初始化串口
  Serial.begin(SERIAL_BAUD_RATE);
  Serial.println("[System] ESP32S3 Motor Controller initialized");
  
  // 初始化电机控制引脚
  initMotors();
  Serial.println("[System] Motor pins initialized");
  
  // 初始化超声传感器引脚
  // 障碍物检测传感器
  initUltrasonicSensor(OBSTACLE_FRONT_TRIG, OBSTACLE_FRONT_ECHO);
  initUltrasonicSensor(OBSTACLE_REAR_TRIG, OBSTACLE_REAR_ECHO);
  initUltrasonicSensor(OBSTACLE_RIGHT_TRIG, OBSTACLE_RIGHT_ECHO);
  // 贴边行驶传感器
  initUltrasonicSensor(EDGE_FRONT_TRIG, EDGE_FRONT_ECHO);
  initUltrasonicSensor(EDGE_MIDDLE_TRIG, EDGE_MIDDLE_ECHO);
  initUltrasonicSensor(EDGE_REAR_TRIG, EDGE_REAR_ECHO);
  Serial.println("[System] Ultrasonic sensors initialized");
  
  // 初始化电池检测引脚
  pinMode(BATTERY_PIN, INPUT);
  Serial.println("[System] Battery sensor initialized");
  
  // 发送系统状态
  String statusJson = "{\"type\":\"status\",\"data\":{\"system\":\"ready\",\"version\":\"1.0.0\"}}";
  Serial.println(statusJson);
}

// 主循环
void loop() {
  // 读取串口命令
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    parseCommand(command);
  }
  
  // 读取传感器数据
  // 障碍物检测传感器
  sensorData.obstacleFront = readUltrasonicDistance(OBSTACLE_FRONT_TRIG, OBSTACLE_FRONT_ECHO);
  sensorData.obstacleRear = readUltrasonicDistance(OBSTACLE_REAR_TRIG, OBSTACLE_REAR_ECHO);
  sensorData.obstacleRight = readUltrasonicDistance(OBSTACLE_RIGHT_TRIG, OBSTACLE_RIGHT_ECHO);
  
  // 贴边行驶传感器
  sensorData.edgeFront = readUltrasonicDistance(EDGE_FRONT_TRIG, EDGE_FRONT_ECHO);
  sensorData.edgeMiddle = readUltrasonicDistance(EDGE_MIDDLE_TRIG, EDGE_MIDDLE_ECHO);
  sensorData.edgeRear = readUltrasonicDistance(EDGE_REAR_TRIG, EDGE_REAR_ECHO);
  
  // 读取电池电量
  sensorData.battery = readBatteryLevel();
  
  // 检测障碍物
  if (detectObstacles()) {
    // 障碍物检测到，停止电机
    setMotorSpeed(0, 0);
    setMotorSpeed(1, 0);
    currentMode = MODE_MANUAL;
    
    // 发送中断信息
    String interruptJson = "{\"type\":\"interrupt\",\"data\":{\"type\":\"obstacle\",\"message\":\"Obstacle detected!\"}}";
    Serial.println(interruptJson);
  } else {
    // 根据当前模式运行
    if (currentMode == MODE_EDGE_FOLLOW) {
      edgeFollowingControl();
    }
  }
  
  // 发送传感器数据（每500ms）
  static unsigned long lastSendTime = 0;
  if (millis() - lastSendTime > 500) {
    sendSensorData();
    lastSendTime = millis();
  }
  
  // 小延迟，稳定系统
  delay(10);
}
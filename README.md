# 基于超声波传感器的智能机器人系统技术文档
# Technical Documentation - Robotized System based on Ultrasonic Sensors

## 目录 / Contents

1. [系统概述 / System Overview](#1-系统概述--system-overview)
2. [硬件架构 / Hardware Architecture](#2-硬件架构--hardware-architecture)
3. [软件架构 / Software Architecture](#3-软件架构--software-architecture)
4. [ROS2节点通信 / ROS2 Node Communication](#4-ros2节点通信--ros2-node-communication)
5. [导航算法 / Navigation Algorithm](#5-导航算法--navigation-algorithm)
6. [数据流 / Data Flow](#6-数据流--data-flow)
7. [系统优化 / System Optimizations](#7-系统优化--system-optimizations)
8. [实施和测试 / Implementation and Testing](#8-实施和测试--implementation-and-testing)
9. [扩展方向 / Expansion Directions](#9-扩展方向--expansion-directions)

## 1. 系统概述 / System Overview

The implemented system represents an autonomous robot capable of navigating through mazes and complex spaces using exclusively ultrasonic sensors for obstacle detection. The system architecture is distributed across two main components that communicate through TCP/IP socket:

- **树莓派服务器 / Raspberry Pi Server**: Collects data from ultrasonic sensors and transmits it to the ROS2 client
- **ROS2客户端 / ROS2 Client**: Processes the received data and implements the navigation algorithm for robot control

This distributed approach allows for a clear separation of responsibilities: Raspberry Pi handles the interaction with hardware sensors, while ROS2 nodes implement the navigation logic and robot control, providing a modular and extensible system.

## 2. 硬件架构 / Hardware Architecture

The system uses the following hardware components:

### 2.1 传感器系统 / Sensor System
- **4个超声波传感器 / 4 Ultrasonic Sensors**:
  - Front sensor: for detecting obstacles in front of the robot
  - Left sensor: for detecting obstacles to the left side
  - Right sensor: for detecting obstacles to the right side
  - Rear sensor: for detecting obstacles behind the robot

### 2.2 计算平台 / Computing Platforms
- **树莓派 / Raspberry Pi**:
  - Manages the ultrasonic sensors
  - Runs the server for data transmission
  - Connected to specified GPIO pins for each sensor
  
- **ROS2主机 / ROS2 Host System**:
  - Runs the ROS2 nodes
  - Implements the navigation logic
  - Communicates with Raspberry Pi through the network

### 2.3 执行器 / Actuators
- **差速驱动系统 / Differential Drive System**:
  - Motors for forward/backward movement
  - Motors for left/right lateral movement
  - Rotation system for changing orientation

### 2.4 连接图 / Connection Diagram

```
+-----------------+        TCP/IP        +------------------+
| Raspberry Pi    | <----------------> | ROS2 Host        |
| Ultrasonic      |     Socket 5000     | Navigation Node  |
| Sensor Server   |                     | Control Node     |
+-----------------+                     +------------------+
       ^                                        |
       |                                        |
       | GPIO                                   | ROS2 Topics
       |                                        V
+-----------------------------------+  +-------------------------+
| Ultrasonic Sensors               |  | Robot Actuators         |
| - Front (Echo: 22, Trigger: 4)   |  | - Linear movement       |
| - Left (Echo: 6, Trigger: 5)     |  | - Angular movement      |
| - Right (Echo: 10, Trigger: 9)   |  | - Obstacle avoidance    |
| - Rear (Echo: 19, Trigger: 13)   |  +-------------------------+
+-----------------------------------+
```

## 3. 软件架构 / Software Architecture

The software architecture is modularized to separate different responsibilities:

### 3.1 树莓派服务器软件 / Raspberry Pi Server Software

The Raspberry Pi server (`ultrasonic_server.py`) implements the following functionalities:

- **传感器初始化 / Sensor Initialization**:
  - Configuration of ultrasonic sensors on the specified GPIO pins
  - Setting of operating parameters

- **数据采集 / Data Acquisition**:
  - Continuous reading of values from all 4 ultrasonic sensors
  - Conversion of values to centimeters

- **数据滤波 / Data Filtering**:
  - Implementation of a low-pass filter for smoothing values
  - Reduction of noise and outlier values
  - Filtering factor configured for balance between reactivity and stability

- **服务器通信 / Server Communication**:
  - Serving TCP connections on port 5000
  - Serialization of data in JSON format
  - Transmission of updated data when significant changes are detected

### 3.2 ROS2客户端软件 / ROS2 Client Software

The ROS2 client (`robot_ultrasonic_client.py`) implements:

- **ROS2节点初始化 / ROS2 Node Initialization**:
  - Creation of the 'robot_controller' node
  - Configuration of publishers for movement commands (`/controller/cmd_vel`)
  - Configuration of subscribers for IMU and odometry data

- **TCP客户端 / TCP Client**:
  - Connecting to the Raspberry Pi server
  - Receiving and deserializing JSON data
  - Updating sensor status in memory

- **状态机导航系统 / State Machine Navigation System**:
  - Implementation of a system with 6 main states
  - Decision logic based on sensor values
  - Loop avoidance algorithm

- **运动控制 / Movement Control**:
  - Generation of `Twist` messages for robot control
  - Adjustment of linear and angular velocity based on environment
  - Recovery strategies for blocked situations

## 4. ROS2节点通信 / ROS2 Node Communication

The system uses the ROS2 infrastructure for communication between components:

### 4.1 发布的主题 / Published Topics
- **/controller/cmd_vel (geometry_msgs/Twist)**:
  - Linear and angular velocity commands for robot control
  - Published by the `robot_controller` node
  - Publication rate: 5Hz (every 0.2 seconds)

### 4.2 订阅的主题 / Subscribed Topics
- **/imu (sensor_msgs/Imu)**:
  - Orientation data from the inertial measurement unit (IMU)
  - Used to determine the current orientation of the robot
  - Processed to extract the yaw angle (rotation around the z-axis)

- **/odom_raw (nav_msgs/Odometry)**:
  - Odometry data for robot position and velocity
  - Used to monitor robot movement
  - Important for detecting blockages and analyzing behavior

### 4.3 节点关系图 / Node Relationship Diagram

```
+-------------------+
| robot_controller  |
+-------------------+
       |  |
       |  |
subscribe |      publish
       |  |
       V  V
+---------+      +-----------+
|  /imu   |      | /cmd_vel  |
+---------+      +-----------+
                       |
+---------+            |
| /odom   |            |
+---------+            V
                 +-------------+
                 | Robot Base  |
                 +-------------+
```

### 4.4 参数配置 / Parameter Configuration
- **导航参数 / Navigation Parameters**:
  - `min_wall_dist`: 15.0 cm - minimum distance from any wall
  - `max_wall_dist`: 30.0 cm - maximum distance to consider a wall exists
  - `exit_detection_dist`: 60.0 cm - distance for exit/open space detection

- **运动参数 / Movement Parameters**:
  - `forward_speed`: 0.08 m/s - normal forward speed
  - `rotation_speed`: 0.25 rad/s - base rotation speed
  - `lateral_speed`: 0.07 m/s - base lateral speed
  - `rotation_tolerance`: 3.0 degrees - tolerance for complete rotation

## 5. 导航算法 / Navigation Algorithm

The navigation algorithm implements a complex state machine that allows the robot to explore unknown environments and avoid obstacles.

### 5.1 状态机 / State Machine
The system uses 6 main states:

1. **EVALUATE**: The robot stops and evaluates all possible directions
2. **MOVE_FORWARD**: Forward movement when the path is clear
3. **MOVE_LEFT**: Lateral movement to the left when the front is blocked but the left is clear
4. **MOVE_RIGHT**: Lateral movement to the right when the front is blocked but the right is clear
5. **MOVE_BACKWARD**: Backward movement when all frontal directions are blocked
6. **RECOVERY**: Recovery strategy when the robot is completely blocked

### 5.2 决策逻辑 / Decision Logic
The algorithm uses the following logic to decide transitions between states:

```
In the EVALUATE state:
    IF front_distance > min_wall_dist THEN
        Transition to MOVE_FORWARD
    ELSE IF left_distance > right_distance AND left_distance > min_wall_dist THEN
        Transition to MOVE_LEFT
    ELSE IF right_distance > left_distance AND right_distance > min_wall_dist THEN
        Transition to MOVE_RIGHT
    ELSE IF rear_distance > min_wall_dist THEN
        Transition to MOVE_BACKWARD
    ELSE
        Transition to RECOVERY
```

### 5.3 循环检测 / Loop Detection
An innovative aspect of the algorithm is the ability to detect and avoid loops - situations where the robot oscillates between the same movements:

- Storing the history of the last decisions (maximum 10)
- Detecting oscillations between states (threshold set at 2 oscillations)
- When a loop is detected, the robot forces a different strategy:
  - Prefers backward movement to exit the loop
  - Resets the decision history after exiting the loop
  - Can temporarily reduce the minimum distance requirements to find an exit

### 5.4 恢复策略 / Recovery Strategy
When the robot reaches a deadlock situation, the RECOVERY state implements:

- Identifying the direction with the most available space
- Attempting to perform a micro-movement in that direction
- If the situation persists, it may try a rotation to change orientation
- Timeout mechanisms to prevent infinite blockages

## 6. 数据流 / Data Flow

The data flow in the system follows a well-defined path:

### 6.1 传感器数据流 / Sensor Data Flow

```
Ultrasonic Sensors --> GPIO Raspberry Pi --> Distance Reading --> Data Filtering
--> JSON Packet Formation --> TCP Socket --> Deserialization in ROS2 client
--> Internal state update in robot_controller
```

### 6.2 控制数据流 / Control Data Flow

```
Navigation Algorithm --> State Decision --> Speed Calculation
--> Publishing Twist message on /controller/cmd_vel --> Motor Drivers
--> Physical Actuation of the robots
```

### 6.3 反馈数据流 / Feedback Data Flow

```
IMU --> /imu topic --> Subscription in robot_controller --> Orientation Update
Encoders --> Odometry --> /odom_raw topic --> Position and Movement Verification
```

### 6.4 数据结构 / Data Structures
Information is transmitted in JSON format between server and client:

```json
{
    "front": 45.23,
    "left": 30.45,
    "right": 12.78,
    "rear": 60.12,
    "timestamp": 1621452687.234
}
```

## 7. 系统优化 / System Optimizations

The system includes multiple optimizations to increase performance and reliability:

### 7.1 传感器数据优化 / Sensor Data Optimization
- **低通滤波 / Low-pass Filter**:
  ```python
  filtered_value = filtering_factor * previous_value + (1 - filtering_factor) * current_value
  ```
  - Reduces noise and sudden variations
  - Filtering factor 0.7 (balance between stability and reactivity)

- **变化检测 / Change Detection**:
  - Transmitting data only when there is a significant change (> 0.5 cm)
  - Reduces network traffic and processor usage

### 7.2 通信优化 / Communication Optimization
- **缓冲区管理 / Buffer Management**:
  - Incremental processing of received data
  - Separation of complete data packets based on newline separator
  - Handling communication errors with automatic retries

- **连接恢复 / Connection Recovery**:
  - Detection of disconnections
  - Automatic retries every 5 seconds
  - Managing connection errors

### 7.3 导航优化 / Navigation Optimization
- **状态转换平滑化 / Smoothing State Transitions**:
  - Complete stop before changing direction
  - Full evaluation of options before making a decision

- **避免振荡 / Avoiding Oscillations**:
  - Detection of oscillation patterns in the decision history
  - Forcing alternative decisions to exit loops

- **安全特性 / Safety Features**:
  - Checking for expired sensor data (2-second timeout)
  - Automatic stop in case of expired data or errors

## 8. 实施和测试 / Implementation and Testing

### 8.1 部署步骤 / Implementation Steps
1. **配置树莓派 / Raspberry Pi Configuration**:
   - Installation of necessary libraries (`gpiozero`, etc.)
   - Connecting sensors to specific GPIO pins
   - Running the `ultrasonic_server.py` script

2. **配置ROS2环境 / ROS2 Environment Configuration**:
   - Installation of ROS2 and required packages
   - Configuration of the ROS2 workspace
   - Building and running the `robot_controller` node

3. **系统集成 / System Integration**:
   - Ensuring network connectivity between Raspberry Pi and the ROS2 system
   - Verifying publishing and subscription to necessary topics
   - Testing socket communication between the two components

### 8.2 测试方法 / Testing Methods
- **传感器测试 / Sensor Testing**:
  - Verification of measurement accuracy
  - Calibration and adjustment of filtering factors

- **导航算法测试 / Navigation Algorithm Testing**:
  - Tests in mazes of different complexities
  - Verification of loop avoidance and recovery behavior

- **长时间运行测试 / Long-term Operation Tests**:
  - Evaluation of system stability over time
  - Detection and correction of potential memory leaks or performance issues

### 8.3 性能指标 / Performance Indicators
- **反应时间 / Reaction Time**: < 200ms from obstacle detection to avoidance decision
- **导航成功率 / Navigation Success Rate**: > 95% in medium complexity mazes
- **循环检测效率 / Loop Detection Efficiency**: Detects and avoids > 90% of potential loop situations
- **连接稳定性 / Connection Stability**: < 1% disconnection rate in normal operation

## 9. 扩展方向 / Expansion Directions

The system was designed to be modular and extensible. Here are some future development directions:

### 9.1 传感器增强 / Sensor Improvement
- Adding additional sensors (LIDAR, cameras, etc.)
- Implementing data fusion for a more robust perception of the environment
- Integration of proximity sensors for precise detection of small objects

### 9.2 算法改进 / Algorithm Improvement
- Implementation of simultaneous localization and mapping algorithms (SLAM)
- Adding trajectory planning using advanced techniques (A*, RRT)
- Integration of machine learning algorithms for adaptation to different environments

### 9.3 系统集成 / System Integration
- Integration with the Nav2 navigation system from ROS2
- Implementation of a remote monitoring and control interface
- Adding advanced telemetry and diagnostic capabilities

### 9.4 应用扩展 / Application Extensions
- Adaptation for autonomous delivery tasks
- Configuration for automatic inspections in industrial environments
- Use in search and rescue scenarios

---

*This documentation was developed for the presentation of the robotized system based on ultrasonic sensors with maze navigation algorithm. All rights reserved © 2025*

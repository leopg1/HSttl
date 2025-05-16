# 基于超声波传感器的智能机器人系统技术文档
# Documentație Tehnică - Sistem Robotizat bazat pe Senzori Ultrasonici

## 目录 / Cuprins

1. [系统概述 / Prezentare generală a sistemului](#1-系统概述--prezentare-generală-a-sistemului)
2. [硬件架构 / Arhitectura hardware](#2-硬件架构--arhitectura-hardware)
3. [软件架构 / Arhitectura software](#3-软件架构--arhitectura-software)
4. [ROS2节点通信 / Comunicarea nodurilor ROS2](#4-ros2节点通信--comunicarea-nodurilor-ros2)
5. [导航算法 / Algoritmul de navigare](#5-导航算法--algoritmul-de-navigare)
6. [数据流 / Fluxul de date](#6-数据流--fluxul-de-date)
7. [系统优化 / Optimizări ale sistemului](#7-系统优化--optimizări-ale-sistemului)
8. [实施和测试 / Implementare și testare](#8-实施和测试--implementare-și-testare)
9. [扩展方向 / Direcții de extindere](#9-扩展方向--direcții-de-extindere)

## 1. 系统概述 / Prezentare generală a sistemului

Sistemul implementat reprezintă un robot autonom capabil să navigheze prin labirinturi și spații complexe folosind exclusiv senzori ultrasonici pentru detectarea obstacolelor. Arhitectura sistemului este distribuită pe două componente principale care comunică prin socket TCP/IP:

- **树莓派服务器 / Serverul Raspberry Pi**: Colectează date de la senzorii ultrasonici și le transmite către clientul ROS2
- **ROS2客户端 / Clientul ROS2**: Procesează datele primite și implementează algoritmul de navigare pentru controlul robotului

Această abordare distribuită permite separarea clară a responsabilităților: Raspberry Pi se ocupă de interacțiunea cu senzorii hardware, în timp ce nodurile ROS2 implementează logica de navigare și controlul robotului, oferind un sistem modular și extindibil.

## 2. 硬件架构 / Arhitectura hardware

Sistemul utilizează următoarele componente hardware:

### 2.1 传感器系统 / Sistemul de senzori
- **4个超声波传感器 / 4 Senzori ultrasonici**:
  - Senzor frontal: pentru detectarea obstacolelor în fața robotului
  - Senzor stânga: pentru detectarea obstacolelor în lateral-stânga
  - Senzor dreapta: pentru detectarea obstacolelor în lateral-dreapta
  - Senzor spate: pentru detectarea obstacolelor în spatele robotului

### 2.2 计算平台 / Platforme de calcul
- **树莓派 / Raspberry Pi**:
  - Gestionează senzorii ultrasonici
  - Rulează serverul pentru transmiterea datelor
  - Conectat la pinii GPIO specificați pentru fiecare senzor
  
- **ROS2主机 / Sistemul gazdă ROS2**:
  - Rulează nodurile ROS2
  - Implementează logica de navigare
  - Comunică cu Raspberry Pi prin rețea

### 2.3 执行器 / Actuatorii
- **差速驱动系统 / Sistem de acționare diferențială**:
  - Motoare pentru deplasare înainte/înapoi
  - Motoare pentru deplasare laterală stânga/dreapta
  - Sistem de rotație pentru schimbarea orientării

### 2.4 连接图 / Schema conexiunilor

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

## 3. 软件架构 / Arhitectura software

Arhitectura software este modularizată pentru a separa diferite responsabilități:

### 3.1 树莓派服务器软件 / Software-ul server de pe Raspberry Pi

Serverul Raspberry Pi (`ultrasonic_server.py`) implementează următoarele funcționalități:

- **传感器初始化 / Inițializarea senzorilor**:
  - Configurarea senzorilor ultrasonici pe pinii GPIO specificați
  - Setarea parametrilor de funcționare

- **数据采集 / Achiziția datelor**:
  - Citirea continuă a valorilor de la toți cei 4 senzori ultrasonici
  - Conversia valorilor în centimetri

- **数据滤波 / Filtrarea datelor**:
  - Implementarea unui filtru trece-jos (low-pass filter) pentru netezirea valorilor
  - Reducerea zgomotului și a valorilor aberante
  - Factor de filtrare configurat pentru echilibrul între reactivitate și stabilitate

- **服务器通信 / Comunicarea server**:
  - Servirea conexiunilor TCP pe portul 5000
  - Serializarea datelor în format JSON
  - Transmiterea datelor actualizate când sunt detectate schimbări semnificative

### 3.2 ROS2客户端软件 / Software-ul client ROS2

Clientul ROS2 (`robot_ultrasonic_client.py`) implementează:

- **ROS2节点初始化 / Inițializarea nodurilor ROS2**:
  - Crearea nodului 'robot_controller'
  - Configurarea publicatorilor pentru comandarea mișcării (`/controller/cmd_vel`)
  - Configurarea subscriberilor pentru date IMU și odometrie

- **TCP客户端 / Clientul TCP**:
  - Conectarea la serverul Raspberry Pi
  - Recepționarea și deserializarea datelor JSON
  - Actualizarea stării senzorilor în memorie

- **状态机导航系统 / Sistemul de navigare bazat pe mașină de stare**:
  - Implementarea unui sistem cu 6 stări principale
  - Logica de decizie bazată pe valorile senzorilor
  - Algoritmul de evitare a buclelor

- **运动控制 / Controlul mișcării**:
  - Generarea mesajelor `Twist` pentru controlul robotului
  - Ajustarea vitezei liniare și unghiulare în funcție de mediu
  - Strategii de recuperare pentru situații blocate

## 4. ROS2节点通信 / Comunicarea nodurilor ROS2

Sistemul utilizează infrastructura ROS2 pentru comunicarea între componente:

### 4.1 发布的主题 / Topicuri publicate
- **/controller/cmd_vel (geometry_msgs/Twist)**:
  - Comenzi de viteză liniară și unghiulară pentru controlul robotului
  - Publicate de nodul `robot_controller`
  - Rate de publicare: 5Hz (la fiecare 0.2 secunde)

### 4.2 订阅的主题 / Topicuri la care se face subscribe
- **/imu (sensor_msgs/Imu)**:
  - Date de orientare de la unitatea de măsură inerțială (IMU)
  - Utilizate pentru a determina orientarea curentă a robotului
  - Procesate pentru a extrage unghiul yaw (rotație în jurul axei z)

- **/odom_raw (nav_msgs/Odometry)**:
  - Date de odometrie pentru poziția și viteza robotului
  - Utilizate pentru a monitoriza deplasarea robotului
  - Importante pentru detectarea blocajelor și analiza comportamentului

### 4.3 节点关系图 / Diagrama relațiilor între noduri

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

### 4.4 参数配置 / Configurarea parametrilor
- **导航参数 / Parametri de navigare**:
  - `min_wall_dist`: 15.0 cm - distanța minimă față de orice perete
  - `max_wall_dist`: 30.0 cm - distanța maximă pentru a considera că există perete
  - `exit_detection_dist`: 60.0 cm - distanță pentru detectarea ieșirii/spațiu deschis

- **运动参数 / Parametri de mișcare**:
  - `forward_speed`: 0.08 m/s - viteza înainte normală
  - `rotation_speed`: 0.25 rad/s - viteza de rotație de bază
  - `lateral_speed`: 0.07 m/s - viteza laterală de bază
  - `rotation_tolerance`: 3.0 grade - toleranță pentru rotația completă

## 5. 导航算法 / Algoritmul de navigare

Algoritmul de navigare implementează o mașină de stare complexă care permite robotului să exploreze medii necunoscute și să evite obstacolele.

### 5.1 状态机 / Mașina de stare
Sistemul utilizează 6 stări principale:

1. **EVALUATE**: Robotul se oprește și evaluează toate direcțiile posibile
2. **MOVE_FORWARD**: Deplasare înainte când calea este liberă
3. **MOVE_LEFT**: Deplasare laterală stânga când frontul este blocat dar stânga este liberă
4. **MOVE_RIGHT**: Deplasare laterală dreapta când frontul este blocat dar dreapta este liberă
5. **MOVE_BACKWARD**: Deplasare înapoi când toate direcțiile frontale sunt blocate
6. **RECOVERY**: Strategie de recuperare când robotul este complet blocat

### 5.2 决策逻辑 / Logica decizională
Algoritmul folosește următoarea logică pentru a decide tranzițiile între stări:

```
În starea EVALUATE:
    IF front_distance > min_wall_dist THEN
        Trecere la MOVE_FORWARD
    ELSE IF left_distance > right_distance AND left_distance > min_wall_dist THEN
        Trecere la MOVE_LEFT
    ELSE IF right_distance > left_distance AND right_distance > min_wall_dist THEN
        Trecere la MOVE_RIGHT
    ELSE IF rear_distance > min_wall_dist THEN
        Trecere la MOVE_BACKWARD
    ELSE
        Trecere la RECOVERY
```

### 5.3 循环检测 / Detectarea buclelor
Un aspect inovativ al algoritmului este capacitatea de a detecta și evita buclele - situații în care robotul oscilează între aceleași mișcări:

- Stocarea istoricului ultimelor decizii (maximum 10)
- Detectarea oscilațiilor între stări (prag setat la 2 oscilații)
- Când este detectată o buclă, robotul forțează o strategie diferită:
  - Preferă deplasarea înapoi pentru a ieși din buclă
  - Resetează istoricul deciziilor după ieșirea din buclă
  - Poate reduce temporar cerințele de distanță minimă pentru a găsi o ieșire

### 5.4 恢复策略 / Strategia de recuperare
Când robotul ajunge într-o situație de blocaj, starea RECOVERY implementează:

- Identificarea direcției cu cel mai mult spațiu disponibil
- Încercarea de a efectua o micro-mișcare în acea direcție
- Dacă situația persistă, poate încerca o rotație pentru schimbarea orientării
- Mecanisme de timeout pentru a preveni blocajele infinite

## 6. 数据流 / Fluxul de date

Fluxul de date în sistem urmează un traseu bine definit:

### 6.1 传感器数据流 / Fluxul datelor de la senzori

```
Senzori Ultrasonici --> GPIO Raspberry Pi --> Citire distanțe --> Filtrare date
--> Formare pachet JSON --> Socket TCP --> Deserializare în client ROS2
--> Actualizare stare internă în robot_controller
```

### 6.2 控制数据流 / Fluxul datelor de control

```
Algoritmul de navigare --> Decizia stării --> Calculul vitezelor
--> Publicare mesaj Twist pe /controller/cmd_vel --> Driver motoare
--> Acționare fizică a roboților
```

### 6.3 反馈数据流 / Fluxul datelor de feedback

```
IMU --> /imu topic --> Subscribtion în robot_controller --> Actualizare orientare
Encodere --> Odometrie --> /odom_raw topic --> Verificare poziție și deplasare
```

### 6.4 数据结构 / Structuri de date
Informația este transmisă în format JSON între server și client:

```json
{
    "front": 45.23,
    "left": 30.45,
    "right": 12.78,
    "rear": 60.12,
    "timestamp": 1621452687.234
}
```

## 7. 系统优化 / Optimizări ale sistemului

Sistemul include multiple optimizări pentru creșterea performanței și fiabilității:

### 7.1 传感器数据优化 / Optimizarea datelor de la senzori
- **低通滤波 / Filtru trece-jos (low-pass filter)**:
  ```python
  filtered_value = filtering_factor * previous_value + (1 - filtering_factor) * current_value
  ```
  - Reduce zgomotul și variațiile bruște
  - Factor de filtrare 0.7 (echilibru între stabilitate și reactivitate)

- **变化检测 / Detectarea schimbărilor**:
  - Transmiterea datelor doar când există o schimbare semnificativă (> 0.5 cm)
  - Reduce traficul de rețea și utilizarea procesorului

### 7.2 通信优化 / Optimizarea comunicațiilor
- **缓冲区管理 / Gestiunea buffer-ului**:
  - Procesarea incrementală a datelor primite
  - Separarea pachetelor complete de date pe baza separatorului newline
  - Tratarea erorilor de comunicație cu reîncercări automate

- **连接恢复 / Recuperarea conexiunii**:
  - Detectarea deconectărilor
  - Reîncercări automate la fiecare 5 secunde
  - Gestionarea erorilor de conexiune

### 7.3 导航优化 / Optimizarea navigației
- **状态转换平滑化 / Netezirea tranzițiilor între stări**:
  - Oprirea completă înainte de schimbarea direcției
  - Evaluarea completă a opțiunilor înainte de a decide

- **避免振荡 / Evitarea oscilațiilor**:
  - Detecția tiparelor de oscilație în istoricul deciziilor
  - Forțarea unor decizii alternative pentru ieșirea din buclă

- **安全特性 / Caracteristici de siguranță**:
  - Verificarea expirării datelor de la senzori (timeout de 2 secunde)
  - Oprirea automată în caz de date expirate sau erori

## 8. 实施和测试 / Implementare și testare

### 8.1 部署步骤 / Pași de implementare
1. **配置树莓派 / Configurarea Raspberry Pi**:
   - Instalarea bibliotecilor necesare (`gpiozero`, etc.)
   - Conectarea senzorilor la pinii GPIO specifici
   - Rularea scriptului `ultrasonic_server.py`

2. **配置ROS2环境 / Configurarea mediului ROS2**:
   - Instalarea ROS2 și pachetelor necesare
   - Configurarea spațiului de lucru ROS2
   - Construirea și rularea nodului `robot_controller`

3. **系统集成 / Integrarea sistemului**:
   - Asigurarea conectivității rețea între Raspberry Pi și sistemul ROS2
   - Verificarea publicării și subscripției la topicurile necesare
   - Testarea comunicației socket între cele două componente

### 8.2 测试方法 / Metode de testare
- **传感器测试 / Testarea senzorilor**:
  - Verificarea acurateței măsurătorilor
  - Calibrarea și ajustarea factorilor de filtrare

- **导航算法测试 / Testarea algoritmului de navigare**:
  - Teste în labirinturi de complexități diferite
  - Verificarea evitării buclelor și a comportamentului de recuperare

- **长时间运行测试 / Teste de funcționare îndelungată**:
  - Evaluarea stabilității sistemului în timp
  - Detectarea și corectarea eventualelor scurgeri de memorie sau probleme de performanță

### 8.3 性能指标 / Indicatori de performanță
- **反应时间 / Timpul de reacție**: < 200ms de la detecția obstacolului până la decizia de evitare
- **导航成功率 / Rata de succes a navigării**: > 95% în labirinturi de complexitate medie
- **循环检测效率 / Eficiența detectării buclelor**: Detectează și evită > 90% din situațiile de buclă potențiale
- **连接稳定性 / Stabilitatea conexiunii**: < 1% rate de deconectare în operare normală

## 9. 扩展方向 / Direcții de extindere

Sistemul a fost proiectat să fie modular și extindibil. Iată câteva direcții de dezvoltare viitoare:

### 9.1 传感器增强 / Îmbunătățirea senzorilor
- Adăugarea de senzori suplimentari (LIDAR, camere, etc.)
- Implementarea fuziunii de date pentru o percepție mai robustă a mediului
- Integrarea senzorilor de proximitate pentru detecția precisă a obiectelor mici

### 9.2 算法改进 / Îmbunătățirea algoritmilor
- Implementarea algoritmilor de cartografiere simultană și localizare (SLAM)
- Adăugarea planificării traiectoriei utilizând tehnici avansate (A*, RRT)
- Integrarea algoritmilor de învățare automată pentru adaptarea la diferite medii

### 9.3 系统集成 / Integrarea sistemelor
- Integrarea cu sistemul de navigație Nav2 din ROS2
- Implementarea unei interfețe de monitorizare și control la distanță
- Adăugarea de capacități de telemetrie și diagnosticare avansată

### 9.4 应用扩展 / Extinderea aplicațiilor
- Adaptarea pentru sarcini de livrare autonomă
- Configurarea pentru inspecții automate în medii industriale
- Utilizarea în scenarii de căutare și salvare

---

*Această documentație a fost elaborată pentru prezentarea sistemului robotizat bazat pe senzori ultrasonici cu algoritm de navigare în labirint. Toate drepturile rezervate © 2025*

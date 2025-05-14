# Proiect Robot Autonom pentru Navigare în Labirint

Acest proiect implementează un robot autonom capabil să navigheze într-un labirint, să detecteze diverse evenimente și să comunice cu o aplicație cloud pentru monitorizare.

## Funcționalități

- Navigare autonomă în labirint folosind LIDAR STL 19P
- Cartografiere SLAM și evitarea obstacolelor
- Detectarea ieșirii marcate cu magneți folosind senzorul Hall KY-024
- Detectarea containerelor cu alcool folosind senzorul MQ-3
- Detectarea denivelarilor folosind senzorul de vibrații SW-420
- Jurnalizarea evenimentelor cu coordonate
- Interfață cloud pentru monitorizare și vizualizare

## Structura Proiectului

```
HS/
├── src/
│   ├── maze_robot/               # Pachetul principal pentru robotul de labirint
│   │   ├── launch/               # Fișiere de lansare
│   │   │   ├── maze_navigation.launch.py  # Lansare navigare
│   │   │   ├── maze_sensors.launch.py     # Lansare senzori
│   │   │   └── cloud_interface.launch.py  # Lansare interfață cloud
│   │   ├── maze_robot/           # Codul sursă Python
│   │   │   ├── hardware/         # Controlere hardware
│   │   │   │   ├── motor_controller.py    # Control motoare
│   │   │   │   ├── lidar_controller.py    # Control LIDAR
│   │   │   │   └── led_controller.py      # Control LED-uri/buzzer
│   │   │   ├── sensors/          # Noduri pentru senzori
│   │   │   │   ├── hall_sensor.py         # Senzor Hall pentru magneți
│   │   │   │   ├── alcohol_sensor.py      # Senzor alcool MQ-3
│   │   │   │   └── vibration_sensor.py    # Senzor vibrații pentru denivelări
│   │   │   ├── navigation/       # Algoritmi de navigare
│   │   │   │   ├── slam.py               # Cartografiere SLAM
│   │   │   │   ├── explorer.py           # Explorare labirint
│   │   │   │   └── path_planner.py       # Planificare traseu
│   │   │   ├── utils/            # Utilități
│   │   │   │   ├── event_logger.py       # Jurnalizare evenimente
│   │   │   │   └── position_tracker.py   # Urmărire poziție
│   │   │   └── cloud/            # Interfață cloud
│   │   │       ├── cloud_interface.py    # Comunicare cu cloud
│   │   │       └── video_stream.py       # Streaming video
│   │   ├── config/               # Fișiere de configurare
│   │   │   ├── lidar_params.yaml        # Parametri LIDAR
│   │   │   ├── navigation_params.yaml   # Parametri navigare
│   │   │   └── sensor_params.yaml       # Parametri senzori
│   │   ├── msg/                  # Mesaje personalizate
│   │   │   └── MazeEvent.msg             # Mesaj pentru evenimente în labirint
│   │   ├── package.xml           # Declarație pachet
│   │   └── setup.py              # Script de instalare
├── maps/                         # Hărți salvate
└── logs/                         # Jurnale de evenimente
```

## Instalare și Configurare

### Instalarea ROS2 Humble pe Raspberry Pi OS

```bash
# Configurarea localizării
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Adăugarea repository-urilor ROS2
sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Instalarea ROS2 Humble
sudo apt update
sudo apt install -y ros-humble-ros-base

# Instalarea dependențelor
sudo apt install -y python3-pip
sudo apt install -y python3-colcon-common-extensions
sudo apt install -y ros-humble-navigation2 ros-humble-nav2-bringup
sudo apt install -y ros-humble-slam-toolbox
pip3 install RPi.GPIO numpy adafruit-blinka adafruit-circuitpython-ads1x15 requests websockets
```

### Construirea proiectului

```bash
cd ~/HS
colcon build
source install/setup.bash
```

### Rularea proiectului

```bash
# Lansarea tuturor componentelor
ros2 launch maze_robot maze_navigation.launch.py
```

## Arhitectura sistemului

Sistemul are trei componente principale:
1. **Navigare și cartografiere** - Folosește LIDAR-ul pentru a construi o hartă a labirintului și a naviga prin el
2. **Detectare evenimente** - Monitorizează senzorii pentru a detecta evenimente (magneți, alcool, denivelări)
3. **Interfață cloud** - Transmite date și imagini către o aplicație cloud pentru monitorizare

## Dezvoltare și testare

Pentru testare, puteți rula nodurile individual folosind:

```bash
ros2 run maze_robot <node_name>
```

Pentru vizualizarea topicurilor active:

```bash
ros2 topic list
```

Pentru monitorizarea unui topic specific:

```bash
ros2 topic echo /<topic_name>
```

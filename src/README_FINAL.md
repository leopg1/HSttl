# Sistem Autonom de Navigare în Labirint pentru Competiție

## Prezentare generală

Acest proiect implementează un sistem complet pentru un robot autonom capabil să navigheze într-un labirint, să detecteze diverse evenimente (magneți, alcool, denivelări) și să transmită informații în timp real către o aplicație cloud pentru monitorizare.

### Specificații pentru competiție:
- Labirintul are coridoare cu lățimea de 35 cm 
- Înălțimea tunelului joasă de 20 cm
- Containere cu apă sau alcool (max. 7 cm înălțime)
- Ieșirea este marcată de doi magneți, unul pe fiecare parte a deschiderii
- Denivelări pe traseu
- Punctul de intrare are coordonatele (0, 0)
- Timpul de evaluare: 15 minute (10 minute alocate pentru completarea labirintului)

## Componente hardware

- **Robot**: Hiwonder Raspberry Pi 5 Robot Car MentorPi M1 cu roți mecanum
- **LIDAR**: STL 19P LDRBOT pentru cartografiere și navigare
- **Senzori**:
  - **Hall Sensor (KY-024)**: Pentru detectarea magneților la ieșire
  - **Senzor de vibrații (SW-420)**: Pentru detectarea denivelarilor
  - **Senzor de alcool (MQ-3)**: Pentru detectarea containerelor cu alcool
  - **Senzor ultrasonic (HC-SR04)**: Pentru măsurarea distanței

## Arhitectura software

Proiectul este implementat folosind ROS2 Humble și constă din următoarele componente principale:

1. **Sistem de cartografiere și navigare**
   - Folosește LIDAR pentru SLAM (Simultaneous Localization and Mapping)
   - Algoritm de explorare pentru descoperirea autonomă a labirintului

2. **Sistem de detectare a evenimentelor**
   - Detectarea magneților pentru identificarea ieșirii
   - Detectarea alcoolului în containere
   - Detectarea denivelarilor

3. **Sistem de înregistrare și comunicare**
   - Jurnalizarea evenimentelor cu coordonatele corespunzătoare
   - Interfață cloud pentru monitorizare și control

## Fișiere principale și structură

- `maze_robot_hardware.py`: Controlul motoarelor, LED-urilor și buzzer-ului
- `maze_navigator.py`: Algoritmii de navigare și explorare
- `maze_sensors.py`: Integrarea și procesarea datelor de la senzori
- `cloud_interface.py`: Comunicarea cu aplicația cloud
- `event_logger.py`: Înregistrarea evenimentelor și generarea rapoartelor
- `launch_maze_navigation.py`: Fișier de lansare pentru întregul sistem

## Instalare pe Raspberry Pi OS

### 1. Instalare ROS2 Humble

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
sudo apt install -y python3-pip python3-numpy
sudo apt install -y python3-colcon-common-extensions
sudo apt install -y ros-humble-slam-toolbox
sudo apt install -y ros-humble-navigation2 ros-humble-nav2-bringup
sudo apt install -y ros-humble-cv-bridge

# Instalarea bibliotecilor pentru senzori
pip3 install RPi.GPIO adafruit-blinka adafruit-circuitpython-ads1x15 websockets
```

### 2. Configurarea proiectului

```bash
# Clonarea proiectului (sau copierea manuală a fișierelor)
mkdir -p ~/maze_robot_ws/src
cd ~/maze_robot_ws/src
# Copiați toate fișierele proiectului aici

# Construirea proiectului
cd ~/maze_robot_ws
colcon build
source install/setup.bash
```

### 3. Configurarea senzorilor

Asigurați-vă că senzorii sunt conectați corect la pinii GPIO:
- Senzor Hall (KY-024): GPIO 17
- Senzor de vibrații (SW-420): GPIO 27
- Senzor de alcool (MQ-3): Conectat la ADC (ADS1115/MCP3008)
- LED-uri: GPIO 18 (R), 23 (G), 24 (B) 
- Buzzer: GPIO 25

## Rularea proiectului

```bash
# Lansarea întregului sistem
ros2 launch ~/maze_robot_ws/launch_maze_navigation.py
```

## Funcționalități principale

### 1. Algoritmul de explorare

Robotul utilizează o strategie de explorare bazată pe detecția frontierelor (granițe între spațiul cunoscut și cel necunoscut). Acesta:
1. Cartografiază spațiul folosind LIDAR
2. Identifică frontierele pentru explorare
3. Planifică și urmează traseele către frontiere
4. Evită obstacolele și impasurile

### 2. Detectarea evenimentelor

- **Magneți (ieșire)**: Când senzorul Hall detectează un magnet, se înregistrează poziția și se verifică prezența celui de-al doilea magnet pentru confirmarea ieșirii.
- **Alcool**: Când senzorul MQ-3 depășește pragul configurat, se înregistrează poziția containerului cu alcool.
- **Denivelări**: Când senzorul de vibrații detectează o denivelare, se înregistrează poziția acesteia.

### 3. Semnalizare și feedback

- **LED-uri**:
  - Roșu: Container cu alcool detectat
  - Verde: Magnet/ieșire detectat(ă)
  - Albastru: Denivelare detectată
- **Buzzer**: Semnale sonore pentru diferite tipuri de evenimente

### 4. Înregistrare și raportare

Toate evenimentele sunt înregistrate cu coordonatele corespunzătoare în fișiere JSON și rezumate în rapoarte text. Rezultatele pot fi vizualizate după finalizarea explorării în directorul `logs/`.

### 5. Interfața cloud

Proiectul include un modul pentru transmiterea datelor către o aplicație cloud prin WebSockets. Acesta transmite:
- Poziția și starea curentă a robotului
- Evenimente detectate în timp real
- Flux video cu overlay de informații

## Optimizare pentru competiție

1. **Calibrarea senzorilor**:
   Ajustați valorile din fișierele de configurare pentru a se potrivi cu senzorii dvs.:
   - Pragul pentru detectarea alcoolului
   - Sensibilitatea senzorului de vibrații

2. **Parametri de navigare**:
   Ajustați parametrii din `maze_navigator.py`:
   - Viteza de explorare
   - Distanța minimă față de obstacole
   - Parametrii algoritmului de frontieră

## Rezolvarea problemelor

### Problema: Robotul nu detectează evenimentele corect
- Verificați conexiunile senzorilor
- Ajustați pragurile de detecție
- Verificați jurnalele de erori

### Problema: Navigația nu funcționează corect
- Verificați dacă LIDAR funcționează și transmite date
- Asigurați-vă că motoarele sunt configurate corect
- Verificați calibrarea odometriei

## Extinderi și îmbunătățiri viitoare

1. Implementarea detectării obiectelor cu camera
2. Algoritmi de navigare mai avansați (A*, D*, RRT)
3. Integrare cu servicii cloud pentru procesare și analiză avansată

---

## Note pentru competiție

- Asigurați-vă că bateria este complet încărcată
- Realizați o calibrare a senzorilor înainte de competiție
- Verificați că robotul poate naviga sub tunelul de 20 cm înălțime
- Activați sistemul de înregistrare a evenimentelor înainte de începerea competiției
- Verificați că ora sistemului este setată corect pentru înregistrarea precisă a evenimentelor

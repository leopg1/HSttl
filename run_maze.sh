#!/bin/bash
# Script pentru rularea robotului de labirint cu ROS2 preinstalat în Terminator

echo "===== Pornire robot pentru navigare autonomă în labirint ====="
echo "Acest script va porni toate componentele necesare pentru explorarea labirintului"

# Obține calea scriptului pentru referințe absolute
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Verifică dacă LD19 este detectat (LIDAR specific MentorPi)
LIDAR_DEVICE="/dev/ttyUSB0"
LIDAR_MODEL="LD19"
if [ -e $LIDAR_DEVICE ]; then
  sudo chmod 666 $LIDAR_DEVICE 2>/dev/null
  echo "LIDAR $LIDAR_MODEL detectat și configurat pe $LIDAR_DEVICE."
else
  echo "ATENȚIE: LIDAR-ul $LIDAR_MODEL nu este detectat pe $LIDAR_DEVICE!"
  echo "Verifică conexiunea LIDAR-ului sau adaptează configurația pentru modelul disponibil."
fi

# Verifică și configurează accesul GPIO
if [ -e /dev/gpiomem ]; then
  sudo chmod a+rw /dev/gpiomem 2>/dev/null
  echo "Acces GPIO configurat pentru senzori."
fi

# Fă toate scripturile Python executabile
find $SCRIPT_DIR/src -name "*.py" -exec chmod +x {} \; 2>/dev/null
echo "Toate scripturile Python au fost făcute executabile."

# Soursează setup-ul pentru mediul ROS2
source $SCRIPT_DIR/setup_ros2.sh

# Configură variabla de mediu LD_LIBRARY_PATH pentru bibliotecile native
if [ -d "/usr/lib/aarch64-linux-gnu" ]; then
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/aarch64-linux-gnu
fi

echo ""
echo "===== MENIU PRINCIPAL ====="
echo "Selectați opțiunea de lansare:"
echo "1. Testare senzori (verifică toți senzorii și actuatorii)"
echo "2. Navigare completă (explorează labirintul și construiește hartă)"
echo "3. Testare LIDAR (doar pentru verificarea LIDAR-ului LD19)"
echo "4. Ieșire"

read -p "Alegere: " option

case $option in
  1)
    echo "Pornire test senzori..."
    if [ -f "$SCRIPT_DIR/src/maze_robot/maze_robot/sensors/sensor_test.py" ]; then
      python3 $SCRIPT_DIR/src/maze_robot/maze_robot/sensors/sensor_test.py
    else
      echo "Eroare: Fișierul sensor_test.py nu a fost găsit!"
      echo "Cale căutată: $SCRIPT_DIR/src/maze_robot/maze_robot/sensors/sensor_test.py"
      exit 1
    fi
    ;;
  2)
    echo "Pornire navigare completă..."
    if [ -f "$SCRIPT_DIR/src/maze_robot/launch/launch_maze_navigation.py" ]; then
      python3 $SCRIPT_DIR/src/maze_robot/launch/launch_maze_navigation.py
    else
      echo "Eroare: Fișierul launch_maze_navigation.py nu a fost găsit!"
      echo "Cale căutată: $SCRIPT_DIR/src/maze_robot/launch/launch_maze_navigation.py"
      exit 1
    fi
    ;;
  3)
    echo "Pornire test LIDAR..."
    if [ -f "$SCRIPT_DIR/src/maze_robot/launch/maze_sensors.launch.py" ]; then
      python3 $SCRIPT_DIR/src/maze_robot/launch/maze_sensors.launch.py
    else
      echo "Eroare: Fișierul maze_sensors.launch.py nu a fost găsit!"
      echo "Cale căutată: $SCRIPT_DIR/src/maze_robot/launch/maze_sensors.launch.py"
      exit 1
    fi
    ;;
  4)
    echo "La revedere!"
    exit 0
    ;;
  *)
    echo "Opțiune invalidă. La revedere!"
    exit 1
    ;;
esac

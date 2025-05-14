#!/bin/bash
# Script pentru pornirea robotului de labirint

echo "===== Pornire robot pentru navigare autonomă în labirint ====="
echo "Acest script va porni toate componentele necesare pentru explorarea labirintului"

# Verifică dacă ROS2 este instalat
if [ -z "$ROS_DISTRO" ]; then
  echo "ROS2 nu pare să fie inițializat. Se încearcă inițializarea..."
  if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
    echo "ROS2 Humble inițializat cu succes."
  else
    echo "EROARE: Nu s-a găsit fișierul de inițializare ROS2. Asigurați-vă că ROS2 Humble este instalat."
    echo "Instalați ROS2 folosind instrucțiunile din README."
    exit 1
  fi
fi

# Verifică dacă sunteți în directorul corect
if [ ! -d "src/maze_robot" ]; then
  echo "EROARE: Nu sunteți în directorul principal al proiectului."
  echo "Rulați acest script din directorul HS."
  exit 1
fi

# Verifică dacă pachetul a fost compilat
if [ ! -d "install" ]; then
  echo "Pachetul nu a fost compilat. Se compilează acum..."
  colcon build
  if [ $? -ne 0 ]; then
    echo "EROARE: Compilarea a eșuat. Verificați erorile de compilare."
    exit 1
  fi
fi

# Inițializare workspace
source install/setup.bash
echo "Workspace-ul a fost inițializat."

# Opțiuni de lansare
echo "Selectați opțiunea de lansare:"
echo "1. Testare senzori (doar pentru verificarea senzorilor și actuatorilor)"
echo "2. Navigare completă (explorare completă a labirintului)"
echo "3. Testare LIDAR (doar pentru verificarea LIDAR-ului)"
echo "4. Ieșire"
read -p "Opțiunea dvs: " option

case $option in
  1)
    echo "Pornire test senzori..."
    ros2 run maze_robot sensor_test
    ;;
  2)
    echo "Pornire navigare completă..."
    ros2 launch maze_robot launch_maze_navigation.py use_cloud:=false
    ;;
  3)
    echo "Pornire test LIDAR..."
    ros2 launch maze_robot launch_maze_navigation.py use_slam:=false use_cloud:=false
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

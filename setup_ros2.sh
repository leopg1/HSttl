#!/bin/bash
# Script personalizat pentru setarea mediului ROS2 în Terminator

# Obține calea completă a directorului scriptului
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Detectează automat variabilele de mediu ROS2 existente
if [ -z "$ROS_DISTRO" ]; then
  export ROS_VERSION=2
  export ROS_PYTHON_VERSION=3
  export ROS_DISTRO=humble
  echo "ROS_DISTRO nu a fost detectat, se folosește implicit 'humble'"
else
  echo "ROS_DISTRO detectat: $ROS_DISTRO"
fi

# Adaugă pachetul tău în PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR/src

# Detectează și folosește AMENT_PREFIX_PATH existent dacă există
if [ -z "$AMENT_PREFIX_PATH" ]; then
  echo "ATENȚIE: AMENT_PREFIX_PATH nu este setat. ROS2 ar putea să nu fie configurat corect."
else
  echo "AMENT_PREFIX_PATH detectat, se continuă cu configurația ROS2 existentă."
fi

# Adaugă comenzi rapide pentru rularea directă
alias ros2_run_maze="python3 $SCRIPT_DIR/src/maze_robot/maze_robot/sensors/sensor_test.py"
alias ros2_launch_maze="python3 $SCRIPT_DIR/src/maze_robot/launch/launch_maze_navigation.py"
alias ros2_test_lidar="python3 $SCRIPT_DIR/src/maze_robot/launch/maze_sensors.launch.py"

# Verifică dispozitivele hardware necesare
echo "Verificare dispozitive hardware..."
if [ -e /dev/ttyUSB0 ]; then
  echo "LIDAR detectat pe /dev/ttyUSB0"
else
  echo "ATENȚIE: LIDAR-ul nu a fost detectat pe /dev/ttyUSB0"
fi

# Setează permisiuni pentru accesul la GPIO și LIDAR
if [ -e /dev/gpiomem ]; then
  sudo chmod a+rw /dev/gpiomem 2>/dev/null
  echo "Permisiuni GPIO configurate"
fi

if [ -e /dev/ttyUSB0 ]; then
  sudo chmod 666 /dev/ttyUSB0 2>/dev/null
  echo "Permisiuni LIDAR configurate"
fi

echo "Mediul pentru proiectul maze_robot a fost configurat cu succes"
echo "Folosește './run_maze.sh' pentru a porni aplicația"

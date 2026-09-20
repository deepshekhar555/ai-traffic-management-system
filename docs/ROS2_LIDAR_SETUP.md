# ROS2 + LiDAR-Camera Perception Setup for this project

This project is working in the current Windows-based Python environment and includes the practical LiDAR-camera fusion upgrade in the Flask dashboard. The full ROS2 C++ stack from the reference repo is not directly installable in this native Windows environment because it depends on Ubuntu/ROS2 and PCL.

Use this setup on WSL2/Ubuntu to run the full reference pipeline.

## 1) Install WSL2 + Ubuntu 24.04

PowerShell as Administrator:

```powershell
wsl --install
wsl --set-default Ubuntu-22.04
```

Then open the Ubuntu terminal and run:

```bash
sudo apt update
sudo apt upgrade -y
```

## 2) Install ROS 2 Jazzy

```bash
sudo apt install curl software-properties-common ca-certificates gnupg lsb-release -y
sudo curl -sSL https://raw.githubusercontent.com/ros2/ros2/master/ros2.repos -o /tmp/ros2.repos
sudo apt update
sudo apt install -y ros-jazzy-desktop
```

If you prefer a minimal install:

```bash
sudo apt install -y ros-jazzy-ros-base
```

## 3) Source ROS

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 4) Install Python + build tooling

```bash
sudo apt install -y python3-pip python3-venv colcon-common-extensions python3-dev build-essential
pip3 install --upgrade pip setuptools wheel
```

## 5) Install ROS2 Python packages used by the LiDAR pipeline

```bash
pip3 install ultralytics numpy<2 opencv-python<4.10.0 psycopg2-binary
```

Also install ROS packages if you want a workspace version of the reference repo:

```bash
sudo apt install -y libpcl-dev pcl-tools ros-jazzy-pcl-conversions ros-jazzy-vision-msgs ros-jazzy-cv-bridge ros-jazzy-sensor-msgs ros-jazzy-visualization-msgs
```

## 6) Clone the reference repo inside WSL

```bash
git clone https://github.com/shadowdk3/LiDAR_Camera_Perception.git
```

Then build the ROS2 package:

```bash
cd LiDAR_Camera_Perception/src/lidar_camera_perception
colcon build --symlink-install
source install/setup.bash
```

## 7) Run the pipeline

Depending on the reference repo launch files, use:

```bash
ros2 launch lidar_camera_perception perception_launch.py
```

## 8) Use it with this project

The current project already includes the Python-compatible adaptation in:

- [backend/src/lidar_camera_perception.py](backend/src/lidar_camera_perception.py)
- [backend/dashboard_app.py](backend/dashboard_app.py)

This is the recommended path for your Windows workspace because it keeps the app working without requiring a ROS runtime on the host OS.

## 9) Recommended next steps

1. Keep the Flask dashboard running in Windows.
2. Use the Python LiDAR+camera fusion endpoint for live scene objects.
3. When you want the full ROS2 pipeline, run the complete reference repo in WSL Ubuntu.
4. Move data or calibration files between environments as needed.

## 10) Validation in this workspace

This project was validated with:

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_lidar_camera_perception_integration.py tests/test_live_camera_telemetry.py tests/test_spatial_perception_stack_port.py -q
```

Result: 3 passed.

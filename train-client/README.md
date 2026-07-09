# TrainClient

## System Preparation for Raspberry Pi 5

### Prerequisites Installation

Before setting up the TrainClient, ensure your Raspberry Pi 5 system has the necessary packages installed.

#### Update System Packages
```bash
sudo apt update
```

#### Install Essential Development Tools
```bash
sudo apt install git
sudo apt install python3-full
sudo apt install python3-pip
sudo apt install python3-venv
sudo apt install -y python3-pyqt5
sudo apt install libcap-dev
sudo apt install python3-picamera2 python3-libcamera libcamera-apps
```

### Python Virtual Environment Setup

Create a dedicated Python virtual environment with system site-packages access:

```bash
sudo apt install python3-venv -y
python3 -m venv rc_venv --system-site-packages
```

#### Virtual Environment Management

**Activation:**
```bash
source /home/reaktor/Python_venv/rc_venv/bin/activate
```

**Deactivation:**
```bash
deactivate
```

### SSH Key Configuration

Set up SSH authentication for secure repository access:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "reaktor@reaktorpi6.local"

# Navigate to SSH directory
cd ~/.ssh

# List generated keys
ls

# Display public key for adding to GitHub/GitLab
cat id_ed25519.pub
```

> **Note:** Copy the output of `cat id_ed25519.pub` and add it to your Git hosting service (GitHub, GitLab, etc.) under SSH keys settings.

### Install necessary libraries on RPi5, Pair Bluetooth devices
```bash
sudo apt install pulseaudio pulseaudio-module-bluetooth bluez-tools pygame
sudo apt install libasound2-dev

sudo systemctl enable bluetooth
sudo systemctl start bluetooth
bluetoothctl show
bluetoothctl
    power on
    agent on
    default-agent
    scan on

pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```




### ROS2 Installation Guide (For Ubuntu system)
```bash
sudo apt install -y curl gnupg2 software-properties-common


## Cleanly re-add the official ROS 2 repository like this:
sudo rm -f /etc/apt/sources.list.d/ros2*
sudo rm -f /usr/share/keyrings/ros-archive-keyring.gpg

sudo apt update
sudo apt install -y curl gnupg2 software-properties-common
sudo add-apt-repository universe


## Add ROS2 Repo
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
| sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
| sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update

## Install
sudo apt install ros-jazzy-rclpy
sudo apt install ros-jazzy-ros-base


## Dependencies
source /opt/ros/jazzy/setup.bash
pip install pyyaml
pip install setuptools
pip install cv_bridge
```


### ROS2 Installation Guide (For Debian based system, Manual process)
```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  git \
  curl \
  wget \
  gnupg2 \
  lsb-release \
  python3-pip \
  python3-venv \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  python3-bloom \
  python3-argcomplete \
  python3-empy \
  python3-numpy \
  libasio-dev \
  libtinyxml2-dev \
  libcunit1-dev

sudo apt install -y python3-rosdep
sudo rosdep init
rosdep update

## this following command must work.. as most of the dependencies are going to install from here
rosdep install --from-paths src --ignore-src -r -y --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers"

## create a new directory
mkdir -p ~/ros2_humble/src
cd ~/ros2_humble

## Fetch the sources
pip3 install -U vcstool
wget https://raw.githubusercontent.com/ros2/ros2/humble/ros2.repos
vcs import src < ros2.repos


## install other dependencies
sudo apt install python3-colcon-common-extensions
sudo apt install libacl1-dev
sudo apt install liblttng-ust-dev lttng-tools libbabeltrace-dev
sudo apt install python3-lark
sudo apt install libeigen3-dev
sudo apt install pkg-config liblttng-ust-dev lttng-tools python3-lttng
sudo apt install liblttng-ctl-dev
sudo apt install libxrandr-dev libx11-dev libxext-dev libxrender-dev
sudo apt install qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools
sudo apt install libfreetype6-dev
pip install pytest


## Start building
cd ~/ros2_humble
colcon build --symlink-install --parallel-workers $(nproc)




## now run Ros2 ENV automatically while system starts
echo "source ~/ros2_humble/install/local_setup.bash" >> ~/.zshrc
source ~/.zshrc

## Check if the installed packages working or not
ros2 run demo_nodes_py listener
ros2 run demo_nodes_cpp talker

```


### Install Lingua Franca
```bash
# debian 12
sudo apt update
sudo apt install openjdk-17-jdk -y

# if debian 13
sudo apt update
sudo apt install -y wget gpg

wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null

echo "deb https://packages.adoptium.net/artifactory/deb trixie main" | sudo tee /etc/apt/sources.list.d/adoptium.list

sudo apt update
sudo apt install temurin-17-jdk


curl -Ls https://install.lf-lang.org | bash -s cli

```
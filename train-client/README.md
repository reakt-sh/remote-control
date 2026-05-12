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
sudo apt install python3-picamera2 pSython3-libcamera libcamera-apps
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


### ROS2 Installation Guide
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

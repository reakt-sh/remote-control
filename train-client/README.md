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
# SSPD - SSH/SCP Project Delivery

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.1--alpha-orange.svg)](https://github.com/MatveyFilippov/SSPD/tree/v2.1.1)

A powerful Python tool for deploying and updating code on remote Unix servers via SSH/SCP. SSPD automates the entire deployment workflow including virtual environment setup, dependency installation, systemd service management, and intelligent file synchronization.

## ✨ Features

- 🚀 **Smart File Sync** - Uploads only changed or missing files using checksum comparison
- 🔧 **Automated Setup** - Creates project directories, virtual environments, and systemd services
- 📦 **Dependency Management** - Automatically installs requirements when `requirements.txt` changes
- 🎮 **Service Control** - Start, stop, and restart remote services with simple commands
- 🎨 **Customizable** - Execute personal commands and create custom deployment workflows
- 📝 **Ignore Patterns** - Supports `.gitignore`-style patterns via `.ignore` file
- 🔌 **Modular Architecture** - Use individual components or complete workflows

## 📋 Prerequisites

- Python 3.11 or higher
- SSH access to remote Unix server
- `sudo` privileges on remote server (for service management)

## 🚀 Quick Start

### Installation

```bash
pip install -U git+https://github.com/MatveyFilippov/SSPD.git
```

#### Installing a Specific Version (tag):

```bash
pip install git+https://github.com/MatveyFilippov/SSPD.git@v2.0.0
```

Replace `v2.0.0` with any available tag (e.g., `v1.3.2`, `v2.1.0`).
Or download and install from [Built Distribution](dist).

#### For development version:

```bash
pip install git+https://github.com/MatveyFilippov/SSPD.git@dev
```

### Basic Usage

```python
import sspd

try:
    # Automatically sync and update remote project
    sspd.tasks.update_remote_project()
finally:
    # Always close connections
    sspd.close_connections()
```

**First run behavior:** SSPD will prompt you for configuration details (host, credentials, paths, etc.) and create `.ini` and `.ignore` files in the `SSPDFiles/` directory.

### Building Custom Workflows

SSPD's modular design allows you to create sophisticated deployment pipelines:

```python
import sspd
from enum import Enum, auto
from typing import NoReturn


class Direction(Enum):
    EXIT = 0
    PUSH_PROJECT = auto()
    PULL_LOGS = auto()
    STOP_RUNNING = auto()
    START_RUNNING = auto()
    DELETE_NOT_REQUIRED_DATA = auto()

    @classmethod
    def get_direction(cls) -> 'Direction':
        """Get user input and return the selected Direction enum."""
        print("Choose what will be done")
        for direction in cls:
            name = direction.name.replace("_", " ").title()
            print(f" * {name} ({direction.value})")
        try:
            return cls(int(input(": ").strip()))
        except ValueError:
            print("No such variant -> exit")
            return cls.EXIT


def delete_not_required_data():
    """Custom sspd task"""
    sspd.tasks.stop_running_remote_service()
    sspd.tasks.execute_command_in_remote_machine(
        command=f"cd /homer/datas && mv new.homer old.homer",
        print_request=False, print_response=False
    )
    status, response = sspd.tasks.execute_command_in_remote_machine(
        command=f"{sspd.base.REMOTE_PROJECT_DIR_PATH}/UserCaches clean", raise_on_error=False
    )
    if status == -1:
        print(f"Something went wrong: {response}")
    sspd.tasks.start_running_remote_service()


HANDLERS = {
    Direction.EXIT: lambda: None,
    Direction.PUSH_PROJECT: sspd.tasks.update_remote_project,
    Direction.DELETE_NOT_REQUIRED_DATA: delete_not_required_data,
    Direction.START_RUNNING: sspd.tasks.start_running_remote_service,
    Direction.STOP_RUNNING: sspd.tasks.stop_running_remote_service,
    Direction.PULL_LOGS: sspd.tasks.download_log_file_from_remote_machine,
}


def main() -> NoReturn:
    try:
        while True:
            user_decision = Direction.get_direction()
            if user_decision == Direction.EXIT:
                break
            HANDLERS[user_decision]()
            print()
    finally:
        sspd.close_connections()


if __name__ == "__main__":
    main()
```

## ⚙️ Configuration

SSPD creates `SSPDFiles/ProjectDelivery.ini` (or `.json`) with the following sections:

#### RemoteMachine
- `USERNAME` - SSH username
- `HOST` - Remote server address
- `PORT` - SSH port (default: 22)
- `PASSWORD` - SSH password

#### CoreProject
- `FILE_TO_RUN` - Main Python file to execute
- `VENV_DIR_NAME` - Virtual environment directory (default: `.venv`)

#### RemoteProject
- `DIR_PATH` - Remote project directory (supports `~/` for home)
- `SERVICE_FILENAME` - Systemd service name
- `LOG_FILE_PATH` - Optional log file path for download

#### LocalProject
- `DIR_PATH` - Local project directory
- `SERVICE_CONTENT_PATH` - Custom service file template (optional)
- `IGNORE_FILE_PATH` - Custom ignore patterns file (default: `SSPDFiles/ProjectDelivery.ignore`)

### Ignore Patterns

Create `SSPDFiles/ProjectDelivery.ignore` to exclude files from synchronization:

```ignorelang
# Python
__pycache__/
*.pyc
.venv/
venv/

# IDE
.idea/
.vscode/

# SSPD
SSPDFiles/

# System
.DS_Store
*.log
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 👤 Author

**homer** - [MatveyFilippov](https://github.com/MatveyFilippov)

## 🙏 Acknowledgments

Built with [Paramiko](https://www.paramiko.org/) for SSH/SCP functionality

---

**Created with ❤️ for developers who deploy to remote servers**
# SSPD - SSH/SFTP Project Delivery

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-orange.svg)](https://github.com/MatveyFilippov/SSPD/tree/v3.0.0)

A powerful Python tool for deploying and updating code on remote Unix servers via SSH/SFTP. SSPD automates the entire deployment workflow including virtual environment setup, dependency installation, systemd service management, and intelligent file synchronization.

## ✨ Features

- 🚀 **Smart File Sync** - Uploads only changed or missing files using checksum comparison
- 🔧 **Automated Setup** - Creates project directories, virtual environments, and systemd services
- 📦 **Dependency Management** - Automatically installs requirements when them changes
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
pip install git+https://github.com/MatveyFilippov/SSPD.git@v3.0.0
```

Replace `v3.0.0` with any available tag (e.g., `v1.3.2`, `v2.1.0`).

#### For development version:

```bash
pip install git+https://github.com/MatveyFilippov/SSPD.git@dev
```

### Basic Usage (CLI)

TODO: [#17](https://github.com/MatveyFilippov/SSPD/issues/17)

**First run behavior:** SSPD will prompt you for configuration details (host, credentials, paths, etc.) and create `.ini` and `.ignore` files in the `SSPDFiles/` directory.

### Building Custom Workflows

SSPD's modular design allows you to create sophisticated deployment pipelines:

```python
from datetime import datetime, timezone
from enum import Enum, auto
import logging
import sys
from typing import NoReturn
import sspd
from sspd.utils.ignore_manager import IgnoreFile


logging.Formatter.formatTime = (
    lambda self, record, datefmt=None: (
        datetime
        .fromtimestamp(record.created, tz=timezone.utc)
        .isoformat(timespec='milliseconds')
    )
)
logging.basicConfig(
    encoding="UTF-8",
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler("sspd.log"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("sspd").setLevel(logging.INFO)


config = sspd.config.Config(
    remote_machine=sspd.config.RemoteMachine(
        username="homer",
        password="secret",
        host="192.168.0.1",
    ),
    remote_project=sspd.config.RemoteProject(
        dir_path="~/MyProject",
        lifecycle=sspd.config.RemoteProjectLifecycleByService(
            service_filename="MyProject.service",
            service_content=None,
        ),
    ),
    local_project=sspd.config.LocalProject(
        dir_path="/Users/homer/Projects/MyProject",
    ),
    core=sspd.config.PythonCore(
        venv_dir_name=".venv",
        executable_file_name="main.py",
        requirements_file_name="requirements.txt",
    ),
)


class Direction(Enum):
    EXIT = 0
    PUSH_PROJECT = auto()
    PULL_LOGS = auto()
    START_RUNNING = auto()
    STOP_RUNNING = auto()
    DELETE_NOT_REQUIRED_DATA = auto()

    @classmethod
    def get_direction(cls) -> 'Direction':
        """Get user input and return the selected Direction enum"""
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
    remote_cache_dir_path = f"{config.remote_project.dir_path.rstrip('/')}/cache"
    response = sspd.execute_command_in_remote_machine(
        command=f"cp {remote_cache_dir_path}/anna /homer/anna.bkp && rm -rf {remote_cache_dir_path}",
        raise_on_error=False,
    )
    if response.status == sspd.RemoteCommandExecutionResponse.Status.ERROR:
        print(f"Something went wrong: {response.message}")


def main() -> NoReturn:
    while True:
        match Direction.get_direction():
            case Direction.EXIT:
                sys.exit(0)
            case Direction.PUSH_PROJECT:
                sspd.tools.delivery_local_project_to_remote_machine()
            case Direction.PULL_LOGS:
                sspd.download_folder_from_remote_machine(
                    remote_folderpath=f"{config.remote_project.dir_path.rstrip('/')}/logs",
                    local_folderpath="logs/prod",
                )
            case Direction.START_RUNNING:
                sspd.tools.start_running_remote_project()
            case Direction.STOP_RUNNING:
                sspd.tools.stop_running_remote_project()
            case Direction.DELETE_NOT_REQUIRED_DATA:
                delete_not_required_data()
        print()


if __name__ == "__main__":
    sspd.initialize(
        config=config,
        ignore_manager=IgnoreFile.create_default_file_if_not_exists("SSPD.ignore"),
    )
    try:
        main()
    finally:
        sspd.clean()
```

## ⚙️ Configuration

To initialize SSPD you have to creates `Config` from [`config`](src/sspd/config.py) with the following sections:

#### RemoteMachine
- `username` - SSH username
- `password` - SSH password
- `host` - Remote server address
- `port` - SSH port (default: `22`)
- `reject_connection_if_unknown_host` - Enable policy for automatically rejecting the unknown hostname & key (default: `True`)

#### RemoteProject
- `dir_path` - Remote project directory (supports `~/` for home)
- `lifecycle` - Remote project lifecycle manager (default: `None`)

#### RemoteProjectLifecycleByService
- `service_filename` - Name of the systemd service file
- `services_dir_path` - Directory where systemd service files are stored (default: `/etc/systemd/system`)
- `service_content` - Custom service file content (default: `None`)

#### LocalProject
- `dir_path` - Local project directory

#### PythonCore
- `venv_dir_name` - Name of the virtual environment directory (default: `.venv`)
- `executable_file_name` - Name of the main executable file (default: `main.py`)
- `requirements_file_name` - Name of the requirements file (default: `None`)

#### Config
- `remote_machine` - Remote machine connection settings (`RemoteMachine`)
- `remote_project` - Remote project settings (`RemoteProject`)
- `local_project` - Local project settings (`LocalProject`)
- `core` - Core language/runtime settings (`PythonCore`, default: `None`)

### Ignore Patterns

Use `IgnoreManager` from [`utils.ignore_manager`](src/sspd/utils/ignore_manager.py) to exclude files from synchronization.
You can choose `SimpleIgnoreManager` (to provide python collection) or `IgnoreFile` (to read collection from file) with patterns:

```ignorelang
# For example:
*.md

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
virtualenv/
pyenv/

# IDE
.idea/
.vscode/

# System
.DS_Store
*.log
.git/
.gitignore
```

## 🤝 Contributing

Contributions are welcome!
Please feel free to submit pull requests or create issues for bugs and feature requests.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 👤 Author

**homer** - [MatveyFilippov](https://github.com/MatveyFilippov)

## 🙏 Acknowledgments

Built with:
- [paramiko](https://pypi.org/project/paramiko/) for SSH/SFTP functionality
- [pathspec](https://pypi.org/project/pathspec/) for delivery file ignore management

---

**Created with ❤️ for developers who deploy to remote servers**
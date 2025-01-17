from . import base, tasks
from .base import close_connections
from . import checker as __checker
import logging


logging.getLogger("paramiko").setLevel(logging.WARNING)


__checker.check_local_project_dir()
__checker.check_remote_project_dir()
__checker.check_remote_venv()
__checker.check_remote_service()

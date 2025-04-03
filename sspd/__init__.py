from . import base, tasks
from .base import close_connections
from .checker import is_remote_file, is_remote_dir
from . import checker as __checker
import logging as __logging


__logging.getLogger("paramiko").setLevel(__logging.WARNING)


__checker.check_local_project_dir()
__checker.check_remote_project_dir()
__checker.check_remote_venv()
__checker.check_remote_service()

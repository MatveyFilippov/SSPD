import logging as __logging
from . import base, checker as __checker, tasks
from .base import close_connections
from .checker import is_remote_dir, is_remote_file
from .utils.paths import FilePath


__logging.getLogger("paramiko").setLevel(__logging.WARNING)

__checker.check_local_project_dir()
__checker.check_remote_project_dir()
__checker.check_remote_venv()
__checker.check_remote_service()

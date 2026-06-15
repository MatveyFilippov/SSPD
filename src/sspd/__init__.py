"""SSH/SCP Project Delivery"""

from .__version__ import __version__, __version_info__
from . import base, tasks
from .base import close_connections
from .checker import is_remote_dir, is_remote_file
from .utils.paths import FilePath


__all__ = [
    "__version__",
    "__version_info__",
    "base",
    "tasks",
    "close_connections",
    "is_remote_dir",
    "is_remote_file",
    "FilePath",
]


from . import checker as __checker

__checker.check_local_project_dir()
__checker.check_remote_project_dir()
__checker.check_remote_venv()
__checker.check_remote_service()

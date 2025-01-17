from . import base, tasks
from . import checker as __checker
import logging


logging.getLogger("paramiko").setLevel(logging.WARNING)


def close_connections():
    try:
        objects_to_close = [base.SSH_REMOTE_MACHINE, base.SFTP_REMOTE_MACHINE]
        for object_to_close in objects_to_close:
            try:
                object_to_close.close()
            except Exception:
                pass
    except Exception:
        pass


__checker.check_local_project_dir()
__checker.check_remote_project_dir()
__checker.check_remote_venv()
__checker.check_remote_service()

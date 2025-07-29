from .. import base, exceptions
import os


def check_local_project_dir():
    if not (os.path.exists(base.LOCAL_PROJECT_DIR_PATH) and os.path.isdir(base.LOCAL_PROJECT_DIR_PATH)):
        raise exceptions.SSPDUnhandleableException(
            f"Invalid local project folder path ('{base.LOCAL_PROJECT_DIR_PATH}')"
        )

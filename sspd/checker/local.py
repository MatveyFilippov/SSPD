import os
from .. import base, exceptions


def check_local_project_dir():
    if not (os.path.exists(base.LOCAL_PROJECT_DIR_PATH) and os.path.isdir(base.LOCAL_PROJECT_DIR_PATH)):
        raise exceptions.SSPDException(f"Invalid local project folder path ('{base.LOCAL_PROJECT_DIR_PATH}')")

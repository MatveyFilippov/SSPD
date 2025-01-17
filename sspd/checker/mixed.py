import os
from .. import base


def is_download_log_file_available() -> bool:
    if not base.REMOTE_LOG_FILE_PATH:
        base.REMOTE_LOG_FILE_PATH = base.config.get_required_value(
            section="RemoteMachine", option="REMOTE_LOG_FILE_PATH"
        ).replace("~/", f"/{base.REMOTE_USERNAME}/")
    if not base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN:
        base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN = base.config.get_required_value(
            section="LocalMachine", option="LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN"
        )
    if not os.path.exists(base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN):
        os.makedirs(os.path.dirname(base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN), exist_ok=True)
    else:
        print(f"File '{base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN}' already exists")
        sign2continue = "Y"
        if input(f"Can I rewrite it ({sign2continue}/n): ").strip() != sign2continue:
            return False
    return True

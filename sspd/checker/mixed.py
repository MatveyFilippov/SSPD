from .. import base
from ..misc_helpers import io
import os


def is_download_log_file_available() -> bool:
    if not base.REMOTE_LOG_FILE_PATH:
        base.REMOTE_LOG_FILE_PATH = base.tilda_replacer(base.config.get_required_value(
            section="RemoteProject", option="LOG_FILE_PATH",
        ))
    if not base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN:
        base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN = base.config.get_required_value(
            section="LocalProject", option="LOG_FILE_PATH_TO_DOWNLOAD_IN",
        )
    if not os.path.exists(base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN):
        os.makedirs(os.path.dirname(base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN), exist_ok=True)
    else:
        io.print_info(f"File '{base.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN}' already exists")
        if not io.input_bool("Can I rewrite it ({sign2continue}/n): ", sign2continue="Y"):
            return False
    return True

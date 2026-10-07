"""SSH/SFTP Project Delivery"""

from . import config, exceptions, tools, utils
from .__version__ import __version__, __stage__, __stage_num__, __version_info__
from .base import initialize, clean
from .core import (
    RemoteCommandExecutionResponse,
    execute_command_in_remote_machine,
    resolve_remote_path,
    is_local_file,
    is_remote_file,
    is_local_folder,
    is_remote_folder,
    get_file_bytes_from_local_machine,
    get_file_bytes_from_remote_machine,
    get_folder_listing_from_local_machine,
    get_folder_listing_from_remote_machine,
    create_folder_in_local_machine,
    create_folder_in_remote_machine,
    download_file_from_remote_machine,
    download_folder_from_remote_machine,
    upload_file_to_remote_machine,
    upload_folder_to_remote_machine,
    delete_file_in_remote_machine,
    delete_folder_in_remote_machine,
)


__all__ = [

    # Version
    "__version__",
    "__stage__",
    "__stage_num__",
    "__version_info__",

    # Modules
    "config",
    "exceptions",
    "tools",
    "utils",

    # Lifecycle
    "initialize",
    "clean",

    # Core tools
    "RemoteCommandExecutionResponse",
    "execute_command_in_remote_machine",
    "resolve_remote_path",
    "is_local_file",
    "is_remote_file",
    "is_local_folder",
    "is_remote_folder",
    "get_file_bytes_from_local_machine",
    "get_file_bytes_from_remote_machine",
    "get_folder_listing_from_local_machine",
    "get_folder_listing_from_remote_machine",
    "create_folder_in_local_machine",
    "create_folder_in_remote_machine",
    "download_file_from_remote_machine",
    "download_folder_from_remote_machine",
    "upload_file_to_remote_machine",
    "upload_folder_to_remote_machine",
    "delete_file_in_remote_machine",
    "delete_folder_in_remote_machine",

]

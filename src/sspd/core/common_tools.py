from enum import IntEnum
import logging
import os
from typing import NamedTuple
from stat import S_ISDIR, S_ISREG
from .connection import get_ssh, get_sftp
from .. import exceptions
from ..utils.paths import get_parent_dir_path


log = logging.getLogger(__name__)


class RemoteCommandExecutionResponse(NamedTuple):
    class Status(IntEnum):
        SUCCESS = 0
        ERROR = -1

    status: Status
    message: str
    notice: str | None


def execute_command_in_remote_machine(command: str, raise_on_error: bool = True) -> RemoteCommandExecutionResponse:
    log.debug(f"Executing command '{command}' in remote machine")

    _, stdout, stderr = get_ssh().exec_command(command)

    er_text = stderr.read().decode().strip()
    notice = None
    if er_text != "":
        if "[notice]" in er_text:
            notice = er_text
        else:
            if raise_on_error:
                raise exceptions.RemoteCommandExecutionException(er_text)
            log.info(f"Faced with error after executing command '{command}' in remote machine")
            return RemoteCommandExecutionResponse(
                status=RemoteCommandExecutionResponse.Status.ERROR,
                message=er_text,
                notice=None,
            )

    response = stdout.read().decode().strip()
    return RemoteCommandExecutionResponse(
        status=RemoteCommandExecutionResponse.Status.SUCCESS,
        message=response,
        notice=notice,
    )


def resolve_remote_path(remote_path: str) -> str:
    log.debug(f"Resolving remote path: '{remote_path}'")
    if not remote_path.startswith("~"):
        return remote_path

    if remote_path == "~" or remote_path.startswith("~/"):
        response = execute_command_in_remote_machine(command="echo $HOME")
        home = response.message.strip()
        if not home:
            raise exceptions.RemotePathException("Cannot resolve remote home directory: empty $HOME")
        if remote_path == "~":
            return home
        return home.rstrip("/") + "/" + remote_path[2:]

    # "~username/..." — not supported here
    raise exceptions.RemotePathException(f"Unsupported tilde expansion for path: '{remote_path}'")


def is_local_file(local_path: str) -> bool:
    log.debug(f"Checking whether '{local_path}' is a local file")
    return os.path.isfile(local_path)


def is_remote_file(remote_path: str) -> bool:
    log.debug(f"Checking whether '{remote_path}' is a remote file")
    path = resolve_remote_path(remote_path)
    try:
        file_attr = get_sftp().stat(path)
        return S_ISREG(file_attr.st_mode)
    except IOError:
        return False


def is_local_folder(local_path: str) -> bool:
    log.debug(f"Checking whether '{local_path}' is a local folder")
    return os.path.isdir(local_path)


def is_remote_folder(remote_path: str) -> bool:
    log.debug(f"Checking whether '{remote_path}' is a remote folder")
    remote_path = resolve_remote_path(remote_path)
    try:
        file_attr = get_sftp().stat(remote_path)
        return S_ISDIR(file_attr.st_mode)
    except IOError:
        return False


def get_file_bytes_from_local_machine(local_filepath: str) -> bytes:
    log.info(f"Getting local '{local_filepath}' file bytes")

    if not is_local_file(local_filepath):
        raise exceptions.LocalFileException(f"No such file '{local_filepath}' in local machine")

    with open(local_filepath, "rb") as local_file:
        return local_file.read()


def get_file_bytes_from_remote_machine(remote_filepath: str) -> bytes:
    log.info(f"Getting remote '{remote_filepath}' file bytes")

    remote_filepath = resolve_remote_path(remote_filepath)

    if not is_remote_file(remote_filepath):
        raise exceptions.RemoteFileException(f"No such file '{remote_filepath}' in remote machine")

    with get_sftp().open(remote_filepath, "r") as remote_file:
        return remote_file.read()


def get_folder_listing_from_local_machine(local_folderpath: str) -> list[str]:
    log.info(f"Getting local '{local_folderpath}' folder listing")

    if not is_local_folder(local_folderpath):
        raise exceptions.LocalFileException(f"No such folder '{local_folderpath}' in local machine")

    return os.listdir(local_folderpath)


def get_folder_listing_from_remote_machine(remote_folderpath: str) -> list[str]:
    log.info(f"Getting remote '{remote_folderpath}' folder listing")

    remote_folderpath = resolve_remote_path(remote_folderpath)

    if not is_remote_folder(remote_folderpath):
        raise exceptions.RemoteFileException(f"No such folder '{remote_folderpath}' in remote machine")

    return get_sftp().listdir(remote_folderpath)


def create_folder_in_local_machine(local_folderpath: str):
    log.debug(f"Creating local folder '{local_folderpath}'")

    if is_local_folder(local_folderpath):
        log.debug(f"Local folder '{local_folderpath}' already created")
        return

    os.makedirs(local_folderpath, exist_ok=True)
    log.info(f"Create local folder '{local_folderpath}'")


def create_folder_in_remote_machine(remote_folderpath: str):
    log.debug(f"Creating remote folder '{remote_folderpath}'")

    remote_folderpath = resolve_remote_path(remote_folderpath)

    if is_remote_folder(remote_folderpath):
        log.debug(f"Remote folder '{remote_folderpath}' already created")
        return

    # get_sftp().mkdir(remote_folderpath)
    execute_command_in_remote_machine(f"mkdir -p {remote_folderpath}")
    log.info(f"Create remote folder '{remote_folderpath}'")


def download_file_from_remote_machine(remote_filepath: str, local_filepath: str):
    log.debug(f"Downloading remote '{remote_filepath}' to local '{local_filepath}'")

    remote_filepath = resolve_remote_path(remote_filepath)

    if not is_remote_file(remote_filepath):
        raise exceptions.RemoteFileException(f"No such file '{remote_filepath}' in remote machine")

    create_folder_in_local_machine(get_parent_dir_path(local_filepath))
    try:
        with open(local_filepath, "wb") as file:
            get_sftp().getfo(remote_filepath, file)
        log.info(f"Download remote '{remote_filepath}' to local '{local_filepath}'")
    except Exception as ex:  # TODO: narrow down exception
        raise exceptions.LocalFileException(f"Can't write '{local_filepath}' in local machine", ex)


def download_folder_from_remote_machine(remote_folderpath: str, local_folderpath: str):
    log.debug(f"Downloading remote '{remote_folderpath}' to local '{local_folderpath}'")

    remote_folderpath = resolve_remote_path(remote_folderpath)

    if not is_remote_folder(remote_folderpath):
        raise exceptions.RemoteFileException(f"No such folder '{remote_folderpath}' in remote machine")

    create_folder_in_local_machine(local_folderpath)
    for item in get_folder_listing_from_remote_machine(remote_folderpath):
        remote_path = os.path.join(remote_folderpath, item)
        local_path = os.path.join(local_folderpath, item)
        if is_remote_folder(remote_path):
            download_folder_from_remote_machine(remote_path, local_path)
        else:
            download_file_from_remote_machine(remote_path, local_path)


def upload_file_to_remote_machine(local_filepath: str, remote_filepath: str):
    log.debug(f"Uploading local '{local_filepath}' to remote '{remote_filepath}'")

    remote_filepath = resolve_remote_path(remote_filepath)

    if not is_local_file(local_filepath):
        raise exceptions.LocalFileException(f"No such file '{local_filepath}' in local machine")

    create_folder_in_remote_machine(get_parent_dir_path(remote_filepath))
    try:
        with open(local_filepath, "rb") as file:
            get_sftp().putfo(file, remote_filepath)
        log.info(f"Upload local '{local_filepath}' to remote '{remote_filepath}'")
    except Exception as ex:  # TODO: narrow down exception
        raise exceptions.RemoteFileException(f"Can't write '{local_filepath}' in remote machine", ex)


def upload_folder_to_remote_machine(local_folderpath: str, remote_folderpath: str):
    log.debug(f"Uploading local '{local_folderpath}' to remote '{remote_folderpath}'")

    remote_folderpath = resolve_remote_path(remote_folderpath)

    if not is_local_folder(local_folderpath):
        raise exceptions.LocalFileException(f"No such folder '{remote_folderpath}' in local machine")

    create_folder_in_remote_machine(remote_folderpath)
    for item in get_folder_listing_from_local_machine(local_folderpath):
        local_path = os.path.join(local_folderpath, item)
        remote_path = os.path.join(remote_folderpath, item)
        if is_local_folder(local_path):
            upload_folder_to_remote_machine(local_path, remote_path)
        else:
            upload_file_to_remote_machine(local_path, remote_path)


def delete_file_in_remote_machine(remote_filepath: str) -> bool:
    log.debug(f"Deleting remote '{remote_filepath}'")

    remote_filepath = resolve_remote_path(remote_filepath)

    if not is_remote_file(remote_filepath):
        return False

    get_sftp().remove(remote_filepath)
    log.info(f"Delete remote '{remote_filepath}'")
    return True


def delete_folder_in_remote_machine(remote_folderpath: str) -> bool:
    log.debug(f"Deleting remote '{remote_folderpath}'")

    remote_folderpath = resolve_remote_path(remote_folderpath)

    if not is_remote_folder(remote_folderpath):
        return False

    for item in get_folder_listing_from_remote_machine(remote_folderpath):
        remote_path = remote_folderpath + "/" + item
        delete_folder_in_remote_machine(remote_path)  # Will skip itself if not a folder
        delete_file_in_remote_machine(remote_path)  # Will skip itself if not a file

    get_sftp().rmdir(remote_folderpath)
    log.info(f"Delete remote '{remote_folderpath}'")
    return True

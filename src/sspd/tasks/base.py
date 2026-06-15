import os
from .. import base, checker, exceptions
from ..utils import io
from ..utils.paths import FilePath


REQUIREMENTS_FILE = FilePath("requirements.txt")


def execute_command_in_remote_machine(
    command: str, raise_on_error: bool = True,
    print_request: bool = True, print_response: bool = True,
) -> tuple[int, str]:
    if print_request:
        io.print_request(command)

    _, stdout, stderr = base.SSH_REMOTE_MACHINE.exec_command(command)

    er_text = stderr.read().decode().strip()
    if er_text != "":
        if "[notice]" in er_text:
            io.print_response(er_text)
        else:
            if raise_on_error:
                raise exceptions.SSPDUnhandleableException(er_text)
            if print_response:
                io.print_response(er_text)
            return -1, er_text

    response = stdout.read().decode().strip()
    if response == "":
        response = "OK"
    if print_response:
        io.print_response(response)

    return 0, response


def download_file_from_remote_machine(remote_filepath: str, local_filepath: str):
    io.print_info(f"Downloading '{remote_filepath}' to '{local_filepath}'")
    try:
        with open(local_filepath, "wb") as file:
            try:
                base.SFTP_REMOTE_MACHINE.getfo(remote_filepath, file)
            except FileNotFoundError:
                raise exceptions.SSPDUnhandleableException(f"No such file '{remote_filepath}' in remote machine")
        io.print_info("Success")
    except FileNotFoundError:
        raise exceptions.SSPDUnhandleableException(f"Can't write '{local_filepath}' in local machine")


def download_folder_from_remote_machine(remote_folderpath: str, local_folderpath: str):
    os.makedirs(local_folderpath, exist_ok=True)
    for item in base.SFTP_REMOTE_MACHINE.listdir(remote_folderpath):
        remote_path = os.path.join(remote_folderpath, item)
        local_path = os.path.join(local_folderpath, item)
        if checker.is_remote_dir(remote_path):
            download_folder_from_remote_machine(remote_path, local_path)
        else:
            download_file_from_remote_machine(remote_path, local_path)


def create_folder_in_remote_machine(remote_folderpath: str):
    if not checker.is_remote_dir(remote_folderpath):
        # base.SFTP_REMOTE_MACHINE.mkdir(remote_folderpath)
        io.print_info(f"Creating remote folder '{remote_folderpath}'")
        execute_command_in_remote_machine(f"mkdir -p {remote_folderpath}")
        io.print_info("Success")


def send_file_to_remote_machine(local_filepath: str, remote_filepath: str):
    create_folder_in_remote_machine(os.path.dirname(remote_filepath))
    try:
        io.print_info(f"Sending '{local_filepath}' to '{remote_filepath}'")
        with open(local_filepath, "rb") as file:
            base.SFTP_REMOTE_MACHINE.putfo(file, remote_filepath)
        io.print_info("Success")
    except FileNotFoundError:
        raise exceptions.SSPDUnhandleableException(f"No such file '{local_filepath}' in local machine")


def send_folder_to_remote_machine(local_folderpath: str, remote_folderpath: str):
    create_folder_in_remote_machine(remote_folderpath)
    for item in os.listdir(local_folderpath):
        local_path = os.path.join(local_folderpath, item)
        remote_path = os.path.join(remote_folderpath, item)
        if os.path.isdir(local_path):
            send_folder_to_remote_machine(local_path, remote_path)
        else:
            send_file_to_remote_machine(local_path, remote_path)


def delete_file_in_remote_machine(remote_filepath: str):
    io.print_info(f"Deleting remote file '{remote_filepath}'")
    if not checker.is_remote_file(remote_filepath):
        raise exceptions.SSPDUnhandleableException(f"No such file '{remote_filepath}' in remote machine")
    base.SFTP_REMOTE_MACHINE.remove(remote_filepath)
    io.print_info("Success")


def delete_folder_in_remote_machine(remote_folderpath: str):
    for item in base.SFTP_REMOTE_MACHINE.listdir(remote_folderpath):
        if checker.is_remote_dir(item):
            delete_folder_in_remote_machine(remote_folderpath)
        delete_file_in_remote_machine(item)
    io.print_info(f"Deleting remote folder '{remote_folderpath}'")
    base.SFTP_REMOTE_MACHINE.rmdir(remote_folderpath)
    io.print_info("Success")


def stop_running_remote_service(raise_on_error: bool = True) -> tuple[int, str]:
    io.print_info("Stop running remote service")
    return execute_command_in_remote_machine(
        f"sudo systemctl stop {base.REMOTE_SERVICE_FILENAME}", raise_on_error=raise_on_error,
    )


def start_running_remote_service(raise_on_error: bool = True) -> tuple[int, str]:
    io.print_info("Start running remote service")
    return execute_command_in_remote_machine(
        f"sudo systemctl start {base.REMOTE_SERVICE_FILENAME}", raise_on_error=raise_on_error,
    )


def restart_running_remote_service(raise_on_error: bool = True) -> tuple[int, str]:
    io.print_info("Reload daemons")
    execute_command_in_remote_machine(f"sudo systemctl daemon-reload")
    io.print_info("Restart running remote service")
    return execute_command_in_remote_machine(
        f"sudo systemctl restart {base.REMOTE_SERVICE_FILENAME}", raise_on_error=raise_on_error,
    )


def run_installing_requirements_in_remote_machine(raise_on_error: bool = True) -> tuple[int, str]:
    io.print_info(f"Try to reinstall requirements in remote '{base.CORE_VENV_DIR_NAME}'")
    return execute_command_in_remote_machine(
        (
            f"{base.REMOTE_PROJECT_DIR_PATH}/{base.CORE_VENV_DIR_NAME}/bin/pip"
            " install -r "
            f"{REQUIREMENTS_FILE.to_absolute(base.REMOTE_PROJECT_DIR_PATH)}"
        ), raise_on_error=raise_on_error,
    )

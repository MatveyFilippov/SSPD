from .. import base, checker, exceptions
from ..misc_helpers import io
from ..misc_helpers.paths import FilePath
import os


REQUIREMENTS_FILE = FilePath("requirements.txt")


def execute_remote_command(command: str, print_request=True, print_response=True,
                           ignore_error=False, in_dir: str | None = None) -> tuple[int, str]:
    if in_dir:
        command = f"cd {in_dir} && {command}"
    if print_request:
        io.print_request(command)
    _, stdout, stderr = base.SSH_REMOTE_MACHINE.exec_command(command)
    er_text = stderr.read().decode().strip()
    if er_text != "":
        if "[notice]" in er_text:
            io.print_response(er_text)
        else:
            if not ignore_error:
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


def download_file_from_remote_server(remote_filepath: str, local_filepath: str):
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


def download_folder_from_remote_server(remote_folderpath: str, local_folderpath: str):
    os.makedirs(local_folderpath, exist_ok=True)
    for item in base.SFTP_REMOTE_MACHINE.listdir(remote_folderpath):
        remote_path = os.path.join(remote_folderpath, item)
        local_path = os.path.join(local_folderpath, item)
        if checker.is_remote_dir(remote_path):
            download_folder_from_remote_server(remote_path, local_path)
        else:
            download_file_from_remote_server(remote_path, local_path)


def send_file_to_remote_server(local_filepath: str, remote_filepath: str):
    try:
        io.print_info(f"Sending '{local_filepath}' to '{remote_filepath}'")
        with open(local_filepath, "rb") as file:
            base.SFTP_REMOTE_MACHINE.putfo(file, remote_filepath)
        io.print_info("Success")
    except FileNotFoundError:
        raise exceptions.SSPDUnhandleableException(f"No such file '{local_filepath}' in local machine")


def stop_running_remote_code():
    io.print_info("Stop running remote py code")
    status, response = execute_remote_command(
        f"sudo systemctl stop {base.REMOTE_SERVICE_FILENAME}", ignore_error=True,
    )
    if status == -1:
        sign2break = "Br"
        print("While stop running was unexpected error, do you want to break process?")
        user_decision = input(f"ENTER (to continue) / '{sign2break}' (to break): ").strip()
        if user_decision == sign2break:
            raise exceptions.SSPDUnhandleableException(response)


def start_running_remote_code():
    io.print_info("Start running remote py code")
    execute_remote_command(f"sudo systemctl start {base.REMOTE_SERVICE_FILENAME}")


def restart_running_remote_code():
    io.print_info("Reload daemons")
    execute_remote_command(f"sudo systemctl daemon-reload")
    io.print_info("Restart running remote py code")
    execute_remote_command(f"sudo systemctl restart {base.REMOTE_SERVICE_FILENAME}")


def run_reinstalling_remote_requirements():
    io.print_info(f"Try to reinstall requirements in remote '{base.REMOTE_VENV_DIR_NAME}'")
    execute_remote_command((
        f"{base.REMOTE_PROJECT_DIR_PATH}/{base.REMOTE_VENV_DIR_NAME}/bin/pip"
        " install -r "
        f"{REQUIREMENTS_FILE.to_absolute(base.REMOTE_PROJECT_DIR_PATH)}"
    ))

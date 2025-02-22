import os
from .. import base, exceptions, misc_helpers, checker


# TODO: here is a lot of print --- make it as param echo=True & add log_echo=False


def execute_remote_command(command: str, print_request=False, print_response=False,
                           ignore_error=False, in_dir: str | None = None) -> tuple[int, str]:
    if in_dir:
        command = f"cd {in_dir} && {command}"
    if print_request:
        misc_helpers.print_request(command)
    _, stdout, stderr = base.SSH_REMOTE_MACHINE.exec_command(command)
    er_text = stderr.read().decode().strip()
    if er_text != "":
        if "[notice]" in er_text:
            misc_helpers.print_response(er_text)
        else:
            if not ignore_error:
                raise exceptions.SSPDUnhandlableException(er_text)
            if print_response:
                misc_helpers.print_response(er_text)
            return -1, er_text
    response = stdout.read().decode().strip()
    if response == "":
        response = "OK"
    if print_response:
        misc_helpers.print_response(response)
    return 0, response


def download_file_from_remote_server(remote_filepath: str, local_filepath: str):
    misc_helpers.print_request(f"Downloading '{remote_filepath}' to '{local_filepath}'")
    try:
        with open(local_filepath, "wb") as file:
            try:
                base.SFTP_REMOTE_MACHINE.getfo(remote_filepath, file)
            except FileNotFoundError:
                raise exceptions.SSPDUnhandlableException(f"No such file '{remote_filepath}' in remote machine")
        misc_helpers.print_response("Success")
    except FileNotFoundError:
        raise exceptions.SSPDUnhandlableException(f"Can't write '{local_filepath}' in local machine")


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
        misc_helpers.print_request(f"Sending '{local_filepath}' to '{remote_filepath}'")
        with open(local_filepath, "rb") as file:
            base.SFTP_REMOTE_MACHINE.putfo(file, remote_filepath)
        misc_helpers.print_response("Success")
    except FileNotFoundError:
        raise exceptions.SSPDUnhandlableException(f"No such file '{local_filepath}' in local machine")


def stop_running_remote_code():
    misc_helpers.print_request("Stop running remote py code")
    status, response = execute_remote_command(
        f"sudo systemctl stop {base.REMOTE_SERVICE_FILENAME}", print_response=True, ignore_error=True,
    )
    if status == -1:
        sign2break = "Br"
        print("While stop running was unexpected error, do you want to break process?")
        user_decision = input(f"ENTER (to continue) / '{sign2break}' (to break): ").strip()
        if user_decision == sign2break:
            raise exceptions.SSPDUnhandlableException(response)


def start_running_remote_code():
    misc_helpers.print_request("Start running remote py code")
    execute_remote_command(f"sudo systemctl start {base.REMOTE_SERVICE_FILENAME}", print_response=True)


def restart_running_remote_code():
    misc_helpers.print_request("Reload daemons")
    execute_remote_command(f"sudo systemctl daemon-reload", print_response=True)
    misc_helpers.print_request("Restart running remote py code")
    execute_remote_command(f"sudo systemctl restart {base.REMOTE_SERVICE_FILENAME}", print_response=True)


def run_reinstalling_remote_requirements():
    misc_helpers.print_request(f"Try to reinstall requirements in remote '{base.REMOTE_VENV_DIR_NAME}'")
    execute_remote_command(
        f"{base.REMOTE_PROJECT_DIR_PATH}/{base.REMOTE_VENV_DIR_NAME}/bin/pip install -r {base.REMOTE_PROJECT_DIR_PATH}/requirements.txt",
        print_response=True
    )

import sspd
from sspd import __backend
from sspd import (
    SSH_REMOTE_MACHINE, REMOTE_PROJECT_PATH, LOCAL_TRACKING_FILES, REMOTE_SERVICE_FILENAME, SFTP_REMOTE_MACHINE,
    REMOTE_VENV_DIR_NAME, LOCAL_PATH_TO_PROJECT_FOLDER,
)


def get_files_list_in_remote_dir(folder_path: str) -> list[str]:
    result = []
    for remote_filename in SFTP_REMOTE_MACHINE.listdir(folder_path):
        remote_absolute_path = folder_path + "/" + remote_filename
        if remote_filename.count("."):
            result.append(remote_absolute_path.replace(f"{REMOTE_PROJECT_PATH}/", ""))
        else:
            if remote_filename == REMOTE_VENV_DIR_NAME:
                continue
            try:
                result += get_files_list_in_remote_dir(remote_absolute_path)
            except FileNotFoundError:
                sspd.exception(f"It isn't a file or folder in remote project dir '{remote_absolute_path}'")
    return result


def get_files_with_diff() -> list[str]:
    result = set()
    remote_files = get_files_list_in_remote_dir(REMOTE_PROJECT_PATH)
    for remote_filename in remote_files:
        if remote_filename in LOCAL_TRACKING_FILES:
            try:
                with open(LOCAL_TRACKING_FILES[remote_filename], "rb") as local_file:
                    local_file_bytes = local_file.read()
                with SFTP_REMOTE_MACHINE.open(REMOTE_PROJECT_PATH+"/"+remote_filename, "r") as remote_file:
                    remote_file_bytes = remote_file.read()
                if __backend.is_files_different(local_file_bytes, remote_file_bytes):
                    result.add(LOCAL_TRACKING_FILES[remote_filename])
            except UnicodeDecodeError:
                result.add(LOCAL_TRACKING_FILES[remote_filename])
    for local_filename, local_filepath in LOCAL_TRACKING_FILES.items():
        if local_filepath not in result and local_filename not in remote_files:
            result.add(local_filepath)
    return list(result)


def run_remote_command(command: str, print_response=False) -> str:
    stdin, stdout, stderr = SSH_REMOTE_MACHINE.exec_command(command)
    er_text = stderr.read().decode().strip()
    if er_text != "":
        if "[notice]" in er_text:
            __backend.print_response(er_text)
        else:
            sspd.exception(er_text)
    response = stdout.read().decode().strip()
    if response == "":
        response = "OK"
    if print_response:
        __backend.print_response(response)
    return response


def makedirs_in_remote_project_folder(path_to_remote_dir: str, print_request_and_response=False):
    dirs = __backend.get_file_path_from_dir(
        from_dir_path=REMOTE_PROJECT_PATH, file_path=path_to_remote_dir
    )
    actual_remote_path = REMOTE_PROJECT_PATH
    for remote_dir in dirs:
        if remote_dir.count(".") and not remote_dir.startswith("."):
            raise ValueError(f"Strange dir '{remote_dir}' (it count '.' in name)")
        remote_dir = actual_remote_path + "/" + remote_dir
        if print_request_and_response:
            __backend.print_request(f"Creating dir '{remote_dir}'")
        run_remote_command(command=f"mkdir -p {remote_dir}", print_response=print_request_and_response)
        actual_remote_path = remote_dir


def send_file_to_remote_server(local_filepath: str, remote_filepath: str):
    try:
        __backend.print_request(f"Sending '{local_filepath}' to '{remote_filepath}'")
        with open(local_filepath, "rb") as file:
            SFTP_REMOTE_MACHINE.putfo(file, remote_filepath)
        __backend.print_response("OK")
    except FileNotFoundError:
        sspd.exception(f"No such file '{local_filepath}' in local dir")


def send_files(local_filepaths: list[str]):
    __backend.print_request("Start sending files from local to remote project dir")
    for local_filepath in local_filepaths:
        local_file_split_path = __backend.get_file_path_from_dir(
            from_dir_path=LOCAL_PATH_TO_PROJECT_FOLDER, file_path=local_filepath
        )
        file_path_from_project_dir = "/".join(local_file_split_path)
        file_path_to_remote_file_dir = "/".join(local_file_split_path[:-1])
        remote_filepath = REMOTE_PROJECT_PATH + "/" + file_path_from_project_dir
        makedirs_in_remote_project_folder(file_path_to_remote_file_dir)
        send_file_to_remote_server(local_filepath, remote_filepath)
    __backend.print_response("All files are send to remote project path")


def stop_running_remote_code():
    __backend.print_request("Stop running remote py code")
    run_remote_command(f'sudo systemctl stop {REMOTE_SERVICE_FILENAME}', print_response=True)


def run_remote_code():
    __backend.print_request("Start running remote py code")
    run_remote_command(f'sudo systemctl start {REMOTE_SERVICE_FILENAME}', print_response=True)


def is_requirements_in_sending_files(sending_files: list[str]) -> bool:
    for file in sending_files:
        if "requirements.txt" in file:
            return True
    return False


def run_reinstalling_remote_requirements():
    __backend.print_request(f"Try to reinstall requirements in remote '{REMOTE_VENV_DIR_NAME}'")
    run_remote_command(
        f'{REMOTE_PROJECT_PATH}/{REMOTE_VENV_DIR_NAME}/bin/pip install -r {REMOTE_PROJECT_PATH}/requirements.txt',
        print_response=True
    )


def update_remote_code():
    print("Start updating remote code")
    print("Look differences in local and remote files")
    updated_files = get_files_with_diff()
    if len(updated_files) == 0:
        print("All files up to date!")
        return
    for updated_file in updated_files:
        print("Update:", updated_file)
    sign2break = "N"
    user_decision = input(f"Are you sure to send all this files to remote server? (y/{sign2break}): ")
    if user_decision.strip() == sign2break:
        print("Break process...")
        return
    print()

    stop_running_remote_code()
    send_files(updated_files)
    if is_requirements_in_sending_files(updated_files):
        run_reinstalling_remote_requirements()
    run_remote_code()
    print()

    print("All is done -> files in remote server are up to date!")

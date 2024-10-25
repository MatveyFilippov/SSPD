import os
import sspd
from sspd import __misc, file_analysing


# TODO: here is a lot of print --- make it as param echo=True & add log_echo=False


def execute_remote_command(command: str, print_request=False, print_response=False,
                           ignore_error=False, in_dir: str | None = None) -> tuple[int, str]:
    if in_dir:
        command = f"cd {in_dir} && {command}"
    if print_request:
        __misc.print_request(command)
    _, stdout, stderr = sspd.SSH_REMOTE_MACHINE.exec_command(command)
    er_text = stderr.read().decode().strip()
    if er_text != "":
        if "[notice]" in er_text:
            __misc.print_response(er_text)
        else:
            if not ignore_error:
                sspd.exception(er_text)
            if print_response:
                __misc.print_response(er_text)
            return -1, er_text
    response = stdout.read().decode().strip()
    if response == "":
        response = "OK"
    if print_response:
        __misc.print_response(response)
    return 0, response


def send_file_to_remote_server(local_filepath: str, remote_filepath: str):
    try:
        __misc.print_request(f"Sending '{local_filepath}' to '{remote_filepath}'")
        with open(local_filepath, "rb") as file:
            sspd.SFTP_REMOTE_MACHINE.putfo(file, remote_filepath)
        __misc.print_response("Success")
    except FileNotFoundError:
        sspd.exception(f"No such file '{local_filepath}' in local dir")


def send_files_from_project_dir(filenames: set[str]):
    __misc.print_request("Start sending files from local to remote project dir")
    for filename in filenames:
        local_filepath = os.path.join(sspd.LOCAL_PROJECT_DIR_PATH, filename)
        remote_filepath = sspd.REMOTE_PROJECT_DIR_PATH + "/" + filename
        execute_remote_command(f"mkdir -p {os.path.dirname(remote_filepath)}")
        send_file_to_remote_server(local_filepath, remote_filepath)
    __misc.print_response("All files are send to remote project dir")


def stop_running_remote_code():
    __misc.print_request("Stop running remote py code")
    status, response = execute_remote_command(
        f"sudo systemctl stop {sspd.REMOTE_SERVICE_FILENAME}", print_response=True, ignore_error=True,
    )
    if status == -1:
        sign2break = "Br"
        print("While stop running was unexpected error, do you want to break process?")
        user_decision = input(f"ENTER (to continue) / '{sign2break}' (to break): ").strip()
        if user_decision == sign2break:
            sspd.exception(response)


def start_running_remote_code():
    __misc.print_request("Start running remote py code")
    execute_remote_command(f"sudo systemctl start {sspd.REMOTE_SERVICE_FILENAME}", print_response=True)


def run_reinstalling_remote_requirements():
    __misc.print_request(f"Try to reinstall requirements in remote '{sspd.REMOTE_VENV_DIR_NAME}'")
    execute_remote_command(
        f"{sspd.REMOTE_PROJECT_DIR_PATH}/{sspd.REMOTE_VENV_DIR_NAME}/bin/pip install -r {sspd.REMOTE_PROJECT_DIR_PATH}/requirements.txt",
        print_response=True
    )


def update_remote_code():
    print("Start updating remote code")
    file_analysing_obj = file_analysing.FileAnalysing(  # TODO: Set here files to ignore (не смотреть файлы которые локально игнорируются)
        sspd.LOCAL_PROJECT_DIR_PATH, sspd.REMOTE_PROJECT_DIR_PATH, sspd.REMOTE_VENV_DIR_NAME,
    )
    print("Look differences in local and remote files")
    files2send = set()
    for new_file in file_analysing_obj.new_files:
        if new_file in sspd.IGNORE.files2ignore:
            continue
        files2send.add(new_file)
        print(" * New:", new_file)
    for updated_file in file_analysing_obj.updated_files:
        if updated_file in sspd.IGNORE.files2ignore:
            continue
        files2send.add(updated_file)
        print(" * Update:", updated_file)
    if len(files2send) == 0:
        print("All files up to date!")
        return
    sign2break = "N"
    user_decision = input(f"Are you sure to send all this files to remote server? (y/{sign2break}): ")
    if user_decision.strip() == sign2break:
        print("Break process...")
        return
    print()

    stop_running_remote_code()
    send_files_from_project_dir(files2send)
    if "requirements.txt" in files2send:
        run_reinstalling_remote_requirements()
    start_running_remote_code()
    print()

    print("All is done -> files in remote server are up to date!")

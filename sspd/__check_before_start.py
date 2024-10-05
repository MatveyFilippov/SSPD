import sspd
import os


def __write_default_service() -> str:
    service_filepath_created_by_sspd = os.path.join(
        "sspd", "SSPD_DefaultServiceFileCreatedInRemoteMachine.service"
    )
    with open(service_filepath_created_by_sspd, "w") as default_service_file:
        default_service_file.write(sspd.DEFAULT_SERVICE_FILE_CONTENT)
    with open(service_filepath_created_by_sspd, "rb") as default_service_file:
        sspd.SFTP_REMOTE_MACHINE.putfo(
            default_service_file, sspd.REMOTE_PATH_TO_SERVICES_DIR + sspd.REMOTE_SERVICE_FILENAME
        )
    sspd.SSH_REMOTE_MACHINE.exec_command("sudo systemctl daemon-reload")
    sspd.SSH_REMOTE_MACHINE.exec_command(f'sudo systemctl enable {sspd.REMOTE_SERVICE_FILENAME}')
    sspd.SSH_REMOTE_MACHINE.exec_command(f'sudo systemctl start {sspd.REMOTE_SERVICE_FILENAME}')
    return service_filepath_created_by_sspd


def check_local_project_dir():
    if not (os.path.exists(sspd.LOCAL_PROJECT_DIR_PATH) and os.path.isdir(sspd.LOCAL_PROJECT_DIR_PATH)):
        sspd.exception(f"Invalid local project folder path ('{sspd.LOCAL_PROJECT_DIR_PATH}')")


def check_remote_project_dir():
    for i in range(2):
        _, _, stderr = sspd.SSH_REMOTE_MACHINE.exec_command(f"cd {sspd.REMOTE_PROJECT_DIR_PATH}")
        if 'No such file or directory' in stderr.read().decode():
            if i == 0:
                sspd.SSH_REMOTE_MACHINE.exec_command(
                    f"mkdir -p {sspd.REMOTE_PROJECT_DIR_PATH}"
                )
            else:
                sspd.exception(f"No working dir ('{sspd.REMOTE_PROJECT_DIR_PATH}') in remote server")


def check_remote_venv():
    for i in range(2):
        _, _, stderr = sspd.SSH_REMOTE_MACHINE.exec_command(
            f"source {sspd.REMOTE_PROJECT_DIR_PATH}/{sspd.REMOTE_VENV_DIR_NAME}/bin/activate"
        )
        if 'No such file or directory' in stderr.read().decode():
            if i == 0:
                print(f"Creating '{sspd.REMOTE_VENV_DIR_NAME}' in remote project dir...")
                _, _, stderr = sspd.SSH_REMOTE_MACHINE.exec_command(
                    f"python3 -m venv {sspd.REMOTE_PROJECT_DIR_PATH}/{sspd.REMOTE_VENV_DIR_NAME}"
                )
                er_text = stderr.read()
                if er_text:
                    sspd.exception(er_text)
            else:
                sspd.exception(f"Virtual environment not exists in working dir '{sspd.REMOTE_PROJECT_DIR_PATH}'")


def check_remote_service():
    try:
        with sspd.SFTP_REMOTE_MACHINE.open(sspd.REMOTE_PATH_TO_SERVICES_DIR + sspd.REMOTE_SERVICE_FILENAME, "r") as remote_file:
            if sspd.DEFAULT_SERVICE_FILE_CONTENT.strip() != remote_file.read().decode().strip():
                raise ValueError("Service file content is not actual")
    except FileNotFoundError:
        er_text = f"File '{sspd.REMOTE_SERVICE_FILENAME}' (service) not exists in remote server"
        print(er_text)
        sign2ignore = "N"
        user_decision = input(f"Can I write default service by myself (y/{sign2ignore}): ")
        if user_decision.strip() == sign2ignore:
            sspd.exception(er_text)
        local_service_cope_filepath = __write_default_service()
        print(f"You can look copy of created service file in '{local_service_cope_filepath}'")
    except ValueError:
        print(f"Content of '{sspd.REMOTE_SERVICE_FILENAME}' (service) is not actual in remote server")
        sign2ignore = "N"
        user_decision = input(f"Can I rewrite default service by myself (y/{sign2ignore}): ")
        if user_decision.strip() != sign2ignore:
            local_service_cope_filepath = __write_default_service()
            print(f"You can look copy of created service file in '{local_service_cope_filepath}'")

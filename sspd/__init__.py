import os
from time import sleep
import paramiko
from sspd.config_file import ConfigFile
from sspd.ignoring_file import IgnoreFile
import logging
from settings import LOGGER_NAME


logging.getLogger("paramiko").setLevel(logging.WARNING)
LOGGER = logging.getLogger(f'{LOGGER_NAME}.SSH_ProjectDelivery')


def close_connections():
    try:
        objects_to_close = [SSH_REMOTE_MACHINE, SFTP_REMOTE_MACHINE]
        for object_to_close in objects_to_close:
            try:
                object_to_close.close()
            except Exception:
                pass
    except Exception:
        pass


def exception(text: str):
    close_connections()
    print("SSH_ProjectDelivery-Exception:", text)
    input("Press ENTER...")
    os.abort()


config = ConfigFile(os.path.join("sspd", "ProjectDelivery.ini"))
REMOTE_IPV4 = config.get_required_value(section="RemoteMachine", option="REMOTE_IPV4")
PASSWORD_TO_REMOTE_SERVER = config.get_required_value(section="RemoteMachine", option="PASSWORD_TO_REMOTE_SERVER")
REMOTE_USERNAME = config.get_required_value(section="RemoteMachine", option="REMOTE_USERNAME")
REMOTE_PROJECT_PATH = config.get_required_value(section="RemoteMachine", option="REMOTE_PROJECT_PATH")
REMOTE_PROJECT_PATH = REMOTE_PROJECT_PATH.replace("~/", f"/{REMOTE_USERNAME}/")
REMOTE_SERVICE_FILENAME = config.get_required_value(section="RemoteMachine", option="REMOTE_SERVICE_FILENAME")
if not REMOTE_SERVICE_FILENAME.endswith(".service"):
    REMOTE_SERVICE_FILENAME += ".service"
REMOTE_PROJECT_FILE_TO_RUN = config.get_required_value(section="RemoteMachine", option="REMOTE_PROJECT_FILE_TO_RUN")
REMOTE_VENV_DIR_NAME = config.get_required_value(section="RemoteMachine", option="REMOTE_VENV_DIR_NAME")
local_machine_section_in_config = "LocalMachine"
local_machine_project_folder_key_in_config = "LOCAL_PATH_TO_PROJECT_FOLDER"
LOCAL_PATH_TO_PROJECT_FOLDER = config.get_required_value(section=local_machine_section_in_config, option=local_machine_project_folder_key_in_config)
if not os.path.exists(LOCAL_PATH_TO_PROJECT_FOLDER):
    exception(f"Invalid folder path (section={local_machine_section_in_config}, value={local_machine_project_folder_key_in_config}) in config file")


ignore = IgnoreFile(
    ignore_filepath=os.path.join("sspd", "ProjectDelivery.ign"),
    project_path=LOCAL_PATH_TO_PROJECT_FOLDER
)
FILES_TO_IGNORE = ignore.files_to_ignore.copy()

LOCAL_TRACKING_FILES = {}
for root, dirs, files in os.walk(LOCAL_PATH_TO_PROJECT_FOLDER):
    for file_name in files:
        filepath = os.path.join(root, file_name)
        if filepath in FILES_TO_IGNORE:
            continue
        LOCAL_TRACKING_FILES[filepath.replace(os.path.join(LOCAL_PATH_TO_PROJECT_FOLDER, ""), "")] = filepath


# Создаем объект SSHClient
SSH_REMOTE_MACHINE = paramiko.SSHClient()
SSH_REMOTE_MACHINE.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    # Подключаемся к серверу
    # TODO: add comments everywhere in SSH_ProjectDelivery (just for future MF)
    SSH_REMOTE_MACHINE.connect(
        hostname=REMOTE_IPV4,
        username=REMOTE_USERNAME,
        password=PASSWORD_TO_REMOTE_SERVER
    )
except paramiko.AuthenticationException:
    exception("Invalid USERNAME or PASSWORD")


# Проверяем существование рабочей директории
stdin, stdout, stderr = SSH_REMOTE_MACHINE.exec_command(f'cd {REMOTE_PROJECT_PATH}')
if 'No such file or directory' in stderr.read().decode():
    exception(f"No working dir ('{REMOTE_PROJECT_PATH}') in remote server")

# Проверяем существование виртуального окружения
stdin, stdout, stderr = SSH_REMOTE_MACHINE.exec_command(f'source {REMOTE_PROJECT_PATH}/{REMOTE_VENV_DIR_NAME}/bin/activate')
if 'No such file or directory' in stderr.read().decode():
    stdin, stdout, stderr = SSH_REMOTE_MACHINE.exec_command(f'python3 -m venv {REMOTE_PROJECT_PATH}/{REMOTE_VENV_DIR_NAME}')
    loading_msg = f"Creating '{REMOTE_VENV_DIR_NAME}' in remote project dir..."
    print(loading_msg, end="")
    sleep(10)
    print("\b"*len(loading_msg), end="")
stdin, stdout, stderr = SSH_REMOTE_MACHINE.exec_command(f'source {REMOTE_PROJECT_PATH}/{REMOTE_VENV_DIR_NAME}/bin/activate')
if 'No such file or directory' in stderr.read().decode():
    exception(f"Virtual environment not exists in working dir '{REMOTE_PROJECT_PATH}'")
SSH_REMOTE_MACHINE.exec_command('deactivate')

# Проверяем существование файлов на сервере
SFTP_REMOTE_MACHINE = SSH_REMOTE_MACHINE.open_sftp()
REMOTE_PATH_TO_SERVICES_DIR = "/etc/systemd/system/"
try:
    SFTP_REMOTE_MACHINE.stat(REMOTE_PATH_TO_SERVICES_DIR + REMOTE_SERVICE_FILENAME)
except FileNotFoundError:
    er_text = f"File '{REMOTE_SERVICE_FILENAME}' (service) not exists in remote server"
    print(er_text)
    sign2break = "N"
    user_decision = input(f"Can I write default service by myself (y/{sign2break}): ")
    if user_decision.strip() == sign2break:
        exception(er_text)

    default_service_script = f"""[Unit]
Description={REMOTE_SERVICE_FILENAME.replace(".service", "")}
After=syslog.target
After=network.target

[Service]
WorkingDirectory={REMOTE_PROJECT_PATH}

User={REMOTE_USERNAME}
Group={REMOTE_USERNAME}

Type=simple
Restart=always
ExecStart={REMOTE_PROJECT_PATH}/{REMOTE_VENV_DIR_NAME}/bin/python3 {REMOTE_PROJECT_PATH}/{REMOTE_PROJECT_FILE_TO_RUN}

[Install]
WantedBy=multi-user.target"""
    service_filename_created_by_ssh_project_delivery = "Service_CreatedBy_SSH_ProjectDelivery.service"
    with open(service_filename_created_by_ssh_project_delivery, "w") as default_service_file:
        default_service_file.write(default_service_script)
    with open(service_filename_created_by_ssh_project_delivery, "rb") as default_service_file:
        SFTP_REMOTE_MACHINE.putfo(default_service_file, REMOTE_PATH_TO_SERVICES_DIR + REMOTE_SERVICE_FILENAME)
    SSH_REMOTE_MACHINE.exec_command('sudo systemctl daemon-reload')
    SSH_REMOTE_MACHINE.exec_command(f'sudo systemctl enable {REMOTE_SERVICE_FILENAME}')
    print(f"You can look created service file in '{os.path.join(os.getcwd(), service_filename_created_by_ssh_project_delivery)}'")

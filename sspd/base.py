from . import exceptions
from .misc_helpers import config_file, ignoring_file
import paramiko
from paramiko.config import SSH_PORT
import os


PROPERTIES_DIR = "SSPDFiles"
os.makedirs(PROPERTIES_DIR, exist_ok=True)


# Get SSPD user settings
config = config_file.ConfigFile(os.path.join(PROPERTIES_DIR, "ProjectDelivery.ini"))
REMOTE_USERNAME = config.get_required_value(section="RemoteMachine", option="USERNAME")
REMOTE_USER_HOME_DIR = f"/{REMOTE_USERNAME}/" if REMOTE_USERNAME == "root" else f"/home/{REMOTE_USERNAME}/"
tilda_replacer = (lambda p: (REMOTE_USER_HOME_DIR + p.removeprefix("~/")) if p.startswith("~/") else p)
REMOTE_MACHINE_HOST = config.get_required_value(section="RemoteMachine", option="HOST")
REMOTE_MACHINE_PORT = config.get_optional_value(section="RemoteMachine", option="PORT", required_type=int)
if REMOTE_MACHINE_PORT is None:
    REMOTE_MACHINE_PORT = SSH_PORT
REMOTE_MACHINE_PASSWORD = config.get_required_value(section="RemoteMachine", option="PASSWORD")
CORE_PROJECT_FILE_TO_RUN = config.get_required_value(section="CoreProject", option="FILE_TO_RUN")
CORE_VENV_DIR_NAME = config.get_required_value(section="CoreProject", option="VENV_DIR_NAME")
while CORE_VENV_DIR_NAME.startswith("/") or CORE_VENV_DIR_NAME.endswith("/"):
    CORE_VENV_DIR_NAME = CORE_VENV_DIR_NAME.removesuffix("/").removeprefix("/")
REMOTE_PROJECT_DIR_PATH = tilda_replacer(config.get_required_value(section="RemoteProject", option="DIR_PATH"))
while REMOTE_PROJECT_DIR_PATH.endswith("/"):
    REMOTE_PROJECT_DIR_PATH = REMOTE_PROJECT_DIR_PATH.removesuffix("/")
REMOTE_SERVICE_FILENAME = config.get_required_value(section="RemoteProject", option="SERVICE_FILENAME")
while REMOTE_SERVICE_FILENAME.startswith("/"):
    REMOTE_SERVICE_FILENAME = REMOTE_SERVICE_FILENAME.removeprefix("/")
if not REMOTE_SERVICE_FILENAME.endswith(".service"):
    REMOTE_SERVICE_FILENAME += ".service"
REMOTE_PATH_TO_SERVICES_DIR = "/etc/systemd/system/"
REMOTE_LOG_FILE_PATH = config.get_optional_value(section="RemoteProject", option="LOG_FILE_PATH")
if REMOTE_LOG_FILE_PATH:
    REMOTE_LOG_FILE_PATH = tilda_replacer(REMOTE_LOG_FILE_PATH)
LOCAL_PROJECT_DIR_PATH = config.get_required_value(section="LocalProject", option="DIR_PATH")
while LOCAL_PROJECT_DIR_PATH.endswith("/"):
    LOCAL_PROJECT_DIR_PATH = LOCAL_PROJECT_DIR_PATH.removesuffix("/")
LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN = config.get_optional_value(section="LocalProject", option="LOG_FILE_PATH_TO_DOWNLOAD_IN")
LOCAL_SERVICE_CONTENT_PATH = config.get_optional_value(section="LocalProject", option="SERVICE_CONTENT_PATH")


# Get filepaths to ignore in SSPD process
IGNORE = ignoring_file.IgnoreFile(
    ignore_filepath=os.path.join(PROPERTIES_DIR, "ProjectDelivery.ign"),
    project_path=LOCAL_PROJECT_DIR_PATH
)


# Init SSH
SSH_REMOTE_MACHINE = paramiko.SSHClient()
SSH_REMOTE_MACHINE.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    # Connect to server
    SSH_REMOTE_MACHINE.connect(
        hostname=REMOTE_MACHINE_HOST,
        port=REMOTE_MACHINE_PORT,
        username=REMOTE_USERNAME,
        password=REMOTE_MACHINE_PASSWORD,
    )
except paramiko.AuthenticationException:
    raise exceptions.SSPDExceptionWithoutClosingConnection("Invalid USERNAME or PASSWORD")

# Init SCP
SFTP_REMOTE_MACHINE = SSH_REMOTE_MACHINE.open_sftp()


local_service_content = None
if LOCAL_SERVICE_CONTENT_PATH:
    with open(LOCAL_SERVICE_CONTENT_PATH, 'r') as file:
        local_service_content = file.read().strip()
SERVICE_CONTENT = local_service_content or f"""[Unit]
Description={REMOTE_SERVICE_FILENAME.removesuffix(".service")}
After=syslog.target
After=network.target

[Service]
WorkingDirectory={REMOTE_PROJECT_DIR_PATH}

User={REMOTE_USERNAME}
Group={REMOTE_USERNAME}

Type=simple
Restart=always
ExecStart={REMOTE_PROJECT_DIR_PATH}/{CORE_VENV_DIR_NAME}/bin/python3 {REMOTE_PROJECT_DIR_PATH}/{CORE_PROJECT_FILE_TO_RUN}

[Install]
WantedBy=multi-user.target"""


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

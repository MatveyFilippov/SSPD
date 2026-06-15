import os
import paramiko
from paramiko.config import SSH_PORT
from . import exceptions
from .utils import config_file, ignoring_file, paths


PROPERTIES_DIR = "SSPDFiles"
os.makedirs(PROPERTIES_DIR, exist_ok=True)

# Get SSPD user settings
config_filepath = os.path.join(PROPERTIES_DIR, "ProjectDelivery.ini")
json_filepath = os.path.join(PROPERTIES_DIR, "ProjectDelivery.json")
if os.path.exists(json_filepath):
    config = config_file.ConfigJSON(json_filepath)
else:
    config = config_file.ConfigFile(config_filepath)

# RemoteMachine settings
REMOTE_USERNAME = config.get(section="RemoteMachine", option="USERNAME")
REMOTE_USER_HOME_DIR = f"/{REMOTE_USERNAME}/" if REMOTE_USERNAME == "root" else f"/home/{REMOTE_USERNAME}/"
tilda_replacer = (lambda p: (REMOTE_USER_HOME_DIR + p.removeprefix("~/")) if p.startswith("~/") else p)
REMOTE_MACHINE_HOST = config.get(section="RemoteMachine", option="HOST")
REMOTE_MACHINE_PORT = int(config.get_optional(section="RemoteMachine", option="PORT", default_value=SSH_PORT, set_default_value_if_not_exists=False))
REMOTE_MACHINE_PASSWORD = config.get(section="RemoteMachine", option="PASSWORD")

# CoreProject settings
CORE_PROJECT_FILE_TO_RUN = config.get(section="CoreProject", option="FILE_TO_RUN")
CORE_VENV_DIR_NAME = paths.normalize_path(config.get_optional(section="CoreProject", option="VENV_DIR_NAME", default_value=".venv"))

# RemoteProject settings
REMOTE_PROJECT_DIR_PATH = paths.normalize_path(tilda_replacer(config.get(section="RemoteProject", option="DIR_PATH")), save_prefix=True)
REMOTE_SERVICE_FILENAME = config.get(section="RemoteProject", option="SERVICE_FILENAME")
REMOTE_PATH_TO_SERVICES_DIR = "/etc/systemd/system/"
REMOTE_LOG_FILE_PATH = config.get_optional(section="RemoteProject", option="LOG_FILE_PATH")
if REMOTE_LOG_FILE_PATH:
    REMOTE_LOG_FILE_PATH = tilda_replacer(REMOTE_LOG_FILE_PATH)

# LocalProject settings
LOCAL_PROJECT_DIR_PATH = paths.normalize_path(config.get(section="LocalProject", option="DIR_PATH"), save_prefix=True)
LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN = config.get_optional(section="LocalProject", option="LOG_FILE_PATH_TO_DOWNLOAD_IN")
LOCAL_SERVICE_CONTENT_PATH = config.get_optional(section="LocalProject", option="SERVICE_CONTENT_PATH")
LOCAL_IGNORE_FILE_PATH = config.get_optional(section="LocalProject", option="IGNORE_FILE_PATH", default_value=os.path.join(PROPERTIES_DIR, "ProjectDelivery.ignore"), set_default_value_if_not_exists=False)


# Get filepaths to ignore in SSPD process
IGNORE = ignoring_file.IgnoreFile(
    ignore_filepath=LOCAL_IGNORE_FILE_PATH,
    project_path=LOCAL_PROJECT_DIR_PATH,
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
        local_service_content = file.read()
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
            except Exception:  # Object can be null or close is not available
                pass
    except Exception:  # Variable can not exist
        pass

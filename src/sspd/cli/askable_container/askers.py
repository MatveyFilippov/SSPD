from dataclasses import fields
from enum import StrEnum
from .container import AskableContainer
from ...config import Config, LocalProject, PythonCore, RemoteMachine, RemoteProject, RemoteProjectLifecycleByService


def get_remote_machine_config(askable_container: AskableContainer) -> RemoteMachine:
    section = "remote_machine"
    remote_machine_fields = {field.name: field for field in fields(RemoteMachine)}
    return RemoteMachine(
        username=askable_container.get(
            section=section,
            option="username",
            value_type=remote_machine_fields["username"].type,
            prompt="RemoteMachine SSH username",
        ),
        password=askable_container.get(
            section=section,
            option="password",
            value_type=remote_machine_fields["password"].type,
            is_secret=True,
            prompt="RemoteMachine SSH password",
        ),
        host=askable_container.get(
            section=section,
            option="host",
            value_type=remote_machine_fields["host"].type,
            prompt="RemoteMachine SSH host",
        ),
        port=askable_container.get_optional(
            section=section,
            option="port",
            value_type=remote_machine_fields["port"].type,
            default_value=remote_machine_fields["port"].default,
            set_default_value_if_not_exists=False,
        ),
        reject_connection_if_unknown_host=askable_container.get_optional(
            section=section,
            option="reject_connection_if_unknown_host",
            value_type=remote_machine_fields["reject_connection_if_unknown_host"].type,
            default_value=remote_machine_fields["reject_connection_if_unknown_host"].default,
            set_default_value_if_not_exists=False,
        ),
    )


class RemoteProjectLifecycleType(StrEnum):
    BY_SERVICE = "remote_project_lifecycle_by_service"
    NONE = ""


def get_remote_project_lifecycle_by_service_config(askable_container: AskableContainer) -> RemoteProjectLifecycleByService:
    section = RemoteProjectLifecycleType.BY_SERVICE.value
    remote_project_lifecycle_by_service_fields = {field.name: field for field in fields(RemoteProjectLifecycleByService)}
    copy_of_service_content_local_filepath = askable_container.get_optional(
        section=section,
        option="copy_of_service_content_local_filepath",
        value_type=str,
        default_value=None,
        set_default_value_if_not_exists=False,
    )
    if copy_of_service_content_local_filepath and copy_of_service_content_local_filepath.lower() != str(None).lower():
        with open(copy_of_service_content_local_filepath, "r", encoding="UTF-8") as service_content_file:
            service_content = service_content_file.read()
    else:
        service_content = None
    return RemoteProjectLifecycleByService(
        service_filename=askable_container.get(
            section=section,
            option="service_filename",
            value_type=remote_project_lifecycle_by_service_fields["service_filename"].type,
            prompt="RemoteProjectLifecycleByService systemd service filename",
        ),
        services_dir_path=askable_container.get_optional(
            section=section,
            option="services_dir_path",
            value_type=remote_project_lifecycle_by_service_fields["services_dir_path"].type,
            default_value=remote_project_lifecycle_by_service_fields["services_dir_path"].default,
            set_default_value_if_not_exists=False,
        ),
        service_content=service_content,
    )


def get_remote_project_lifecycle_config(lifecycle_type: RemoteProjectLifecycleType, askable_container: AskableContainer) -> RemoteProjectLifecycleByService | None:
    match lifecycle_type:
        case RemoteProjectLifecycleType.BY_SERVICE:
            return get_remote_project_lifecycle_by_service_config(askable_container)
        case RemoteProjectLifecycleType.NONE:
            return None


def get_remote_project_config(askable_container: AskableContainer) -> RemoteProject:
    section = "remote_project"
    remote_project_fields = {field.name: field for field in fields(RemoteProject)}
    lifecycle_type_str = askable_container.get(
        section=section,
        option="lifecycle_type",
        value_type=str,
        prompt="RemoteProject lifecycle type",
        choices=tuple(lifecycle.name.lower() for lifecycle in RemoteProjectLifecycleType),
    ).upper()
    try:
        lifecycle_type = RemoteProjectLifecycleType[lifecycle_type_str]
    except KeyError:
        lifecycle_type = RemoteProjectLifecycleType.NONE
    return RemoteProject(
        dir_path=askable_container.get(
            section=section,
            option="dir_path",
            value_type=remote_project_fields["dir_path"].type,
            prompt="RemoteProject directory path",
        ),
        lifecycle=get_remote_project_lifecycle_config(
            lifecycle_type=lifecycle_type,
            askable_container=askable_container,
        ),
    )


def get_local_project_config(askable_container: AskableContainer) -> LocalProject:
    section = "local_project"
    local_project_fields = {field.name: field for field in fields(LocalProject)}
    return LocalProject(
        dir_path=askable_container.get(
            section=section,
            option="dir_path",
            value_type=local_project_fields["dir_path"].type,
            prompt="LocalProject directory path",
        )
    )


class CoreType(StrEnum):
    PYTHON = "python_core"
    NONE = ""


def get_python_core_config(askable_container: AskableContainer) -> PythonCore:
    section = CoreType.PYTHON.value
    python_core_fields = {field.name: field for field in fields(PythonCore)}
    return PythonCore(
        venv_dir_name=askable_container.get_optional(
            section=section,
            option="venv_dir_name",
            value_type=python_core_fields["venv_dir_name"].type,
            default_value=python_core_fields["venv_dir_name"].default,
            set_default_value_if_not_exists=True,
        ),
        executable_file_name=askable_container.get_optional(
            section=section,
            option="executable_file_name",
            value_type=python_core_fields["executable_file_name"].type,
            default_value=python_core_fields["executable_file_name"].default,
            set_default_value_if_not_exists=True,
        ),
        requirements_file_name=askable_container.get_optional(
            section=section,
            option="requirements_file_name",
            value_type=python_core_fields["requirements_file_name"].type,
            default_value=python_core_fields["requirements_file_name"].default,
            set_default_value_if_not_exists=False,
        ),
    )


def get_core_config(askable_container: AskableContainer) -> PythonCore | None:
    core_type_str = askable_container.get(
        section="core",
        option="type",
        value_type=str,
        prompt="Core type",
        choices=tuple(core.name.lower() for core in CoreType),
    ).upper()
    try:
        core_type = CoreType[core_type_str]
    except KeyError:
        core_type = CoreType.NONE

    match core_type:
        case CoreType.PYTHON:
            return get_python_core_config(askable_container)
        case CoreType.NONE:
            return None


def get_config(askable_container: AskableContainer) -> Config:
    return Config(
        remote_machine=get_remote_machine_config(askable_container),
        remote_project=get_remote_project_config(askable_container),
        local_project=get_local_project_config(askable_container),
        core=get_core_config(askable_container),
    )

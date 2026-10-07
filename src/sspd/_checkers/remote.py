import shlex
from ..config import PythonCore, RemoteProject, RemoteProjectLifecycleByService
from ..core import is_remote_folder, is_remote_file, execute_command_in_remote_machine
from ..exceptions import CheckFailedException


class RemoteProjectChecker:
    class RemoteProjectLifecycleByServiceChecker:
        @staticmethod
        def _get_remote_service_file_content(remote_service_file_path: str) -> str:
            safe_remote_service_file_path = shlex.quote(remote_service_file_path)
            response = execute_command_in_remote_machine(command=f"cat {safe_remote_service_file_path}")
            return response.message

        @classmethod
        def check_remote_project_lifecycle_by_service(cls, remote_project_lifecycle_by_service_config: RemoteProjectLifecycleByService):
            if not remote_project_lifecycle_by_service_config.service_filename.strip():  # If blank
                raise CheckFailedException("Invalid service file name, string is blank")

            if not remote_project_lifecycle_by_service_config.services_dir_path.strip():  # If blank
                raise CheckFailedException("Invalid services directory path, string is blank")

            remote_service_file_path = (
                    remote_project_lifecycle_by_service_config.services_dir_path.rstrip("/") +
                    "/" +
                    remote_project_lifecycle_by_service_config.service_filename
            )

            if not is_remote_file(remote_service_file_path):
                raise CheckFailedException(f"Service file does not exist in remote machine: '{remote_service_file_path}'")

            if remote_project_lifecycle_by_service_config.service_content is not None:
                actual_service_content = cls._get_remote_service_file_content(
                    remote_service_file_path=remote_service_file_path,
                )
                if actual_service_content.strip() != remote_project_lifecycle_by_service_config.service_content.strip():
                    raise CheckFailedException(f"Content of service file is not actual in remote machine: '{remote_service_file_path}'")

    @staticmethod
    def check_remote_project_dir(remote_project_dir_path: str):
        if not is_remote_folder(remote_project_dir_path):
            raise CheckFailedException(f"Invalid remote project directory path, no such folder: '{remote_project_dir_path}'")

    @classmethod
    def check_remote_project(cls, remote_project_config: RemoteProject):
        cls.check_remote_project_dir(
            remote_project_dir_path=remote_project_config.dir_path,
        )
        if isinstance(remote_project_config.lifecycle, RemoteProjectLifecycleByService):
            cls.RemoteProjectLifecycleByServiceChecker.check_remote_project_lifecycle_by_service(
                remote_project_lifecycle_by_service_config=remote_project_config.lifecycle,
            )


class RemoteCoreChecker:
    class RemotePythonCoreChecker:
        @classmethod
        def check_remote_venv_dir(cls, venv_dir_name: str, remote_project_dir_path: str):
            remote_venv_dir_path = remote_project_dir_path + "/" + venv_dir_name
            if not is_remote_folder(remote_venv_dir_path):
                raise CheckFailedException(f"Python virtual environment '{venv_dir_name}' does not exist in remote project: '{remote_project_dir_path}'")

            remote_venv_python_file_path = remote_venv_dir_path + "/bin/python3"
            if not is_remote_file(remote_venv_python_file_path):
                raise CheckFailedException(f"Python file does not exist in remote project virtual environment: '{remote_venv_python_file_path}'")

        @staticmethod
        def check_remote_executable_file(executable_file_name: str, remote_project_dir_path: str):
            if not executable_file_name.strip():  # If blank
                raise CheckFailedException("Invalid python executable file name, string is blank")

            remote_executable_file_path = remote_project_dir_path + "/" + executable_file_name
            # Absence of remote executable file is allowed (if not synchronized yet), no checking...

        @staticmethod
        def check_remote_requirements_file(requirements_file_name: str | None, remote_project_dir_path: str):
            if requirements_file_name is None:
                return

            if not requirements_file_name.strip():  # If blank
                raise CheckFailedException("Invalid python requirements file name, string is blank")

            remote_requirements_file_path = remote_project_dir_path + "/" + requirements_file_name
            # Absence of remote requirements file is allowed (if not synchronized yet), no checking...

        @classmethod
        def check_remote_python_core_config(cls, remote_core_config: PythonCore, remote_project_dir_path: str):
            cls.check_remote_venv_dir(
                venv_dir_name=remote_core_config.venv_dir_name,
                remote_project_dir_path=remote_project_dir_path,
            )
            cls.check_remote_executable_file(
                executable_file_name=remote_core_config.executable_file_name,
                remote_project_dir_path=remote_project_dir_path,
            )
            cls.check_remote_requirements_file(
                requirements_file_name=remote_core_config.requirements_file_name,
                remote_project_dir_path=remote_project_dir_path,
            )

    @classmethod
    def check_remote_core_config(cls, remote_core_config: PythonCore | None, remote_project_dir_path: str):
        if isinstance(remote_core_config, PythonCore):
            cls.RemotePythonCoreChecker.check_remote_python_core_config(
                remote_core_config=remote_core_config,
                remote_project_dir_path=remote_project_dir_path,
            )


def check_remote(remote_project_config: RemoteProject, remote_core_config: PythonCore | None):
    RemoteProjectChecker.check_remote_project(
        remote_project_config=remote_project_config,
    )
    RemoteCoreChecker.check_remote_core_config(
        remote_core_config=remote_core_config,
        remote_project_dir_path=remote_project_config.dir_path,
    )

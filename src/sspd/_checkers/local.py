import os
from ..config import LocalProject, PythonCore
from ..core import is_local_folder, is_local_file
from ..exceptions import CheckFailedException


class LocalProjectChecker:
    @staticmethod
    def check_local_project_dir(local_project_dir_path: str):
        if not is_local_folder(local_project_dir_path):
            raise CheckFailedException(f"Invalid local project directory path, no such folder: '{local_project_dir_path}'")

    @classmethod
    def check_local_project(cls, local_project_config: LocalProject):
        cls.check_local_project_dir(
            local_project_dir_path=local_project_config.dir_path,
        )


class LocalCoreChecker:
    class LocalPythonCoreChecker:
        @staticmethod
        def check_local_venv_dir(venv_dir_name: str, local_project_dir_path: str):
            if not venv_dir_name.strip():  # If blank
                raise CheckFailedException("Invalid python virtual environment directory name, string is blank")

            local_venv_dir_path = os.path.join(local_project_dir_path, venv_dir_name)
            # Absence of local virtual environment is allowed, no checking...

        @staticmethod
        def check_local_executable_file(executable_file_name: str, local_project_dir_path: str):
            local_executable_file_path = os.path.join(local_project_dir_path, executable_file_name)
            if not is_local_file(local_executable_file_path):
                raise CheckFailedException(f"Invalid python executable file name, no such file '{executable_file_name}' in local project: '{local_project_dir_path}'")

        @staticmethod
        def check_local_requirements_file(requirements_file_name: str | None, local_project_dir_path: str):
            if requirements_file_name is None:
                return

            if not requirements_file_name.strip():  # If blank
                raise CheckFailedException("Invalid python requirements file name, string is blank")

            local_requirements_file_path = os.path.join(local_project_dir_path, requirements_file_name)
            # Absence of local requirements file is allowed, no checking...

        @classmethod
        def check_local_python_core(cls, local_core_config: PythonCore, local_project_dir_path: str):
            cls.check_local_venv_dir(
                venv_dir_name=local_core_config.venv_dir_name,
                local_project_dir_path=local_project_dir_path,
            )
            cls.check_local_executable_file(
                executable_file_name=local_core_config.executable_file_name,
                local_project_dir_path=local_project_dir_path,
            )
            cls.check_local_requirements_file(
                requirements_file_name=local_core_config.requirements_file_name,
                local_project_dir_path=local_project_dir_path,
            )

    @classmethod
    def check_local_core(cls, local_core_config: PythonCore | None, local_project_dir_path: str):
        if isinstance(local_core_config, PythonCore):
            cls.LocalPythonCoreChecker.check_local_python_core(
                local_core_config=local_core_config, local_project_dir_path=local_project_dir_path
                )


def check_local(local_project_config: LocalProject, local_core_config: PythonCore | None):
    LocalProjectChecker.check_local_project(
        local_project_config=local_project_config,
    )
    LocalCoreChecker.check_local_core(
        local_core_config=local_core_config,
        local_project_dir_path=local_project_config.dir_path,
    )

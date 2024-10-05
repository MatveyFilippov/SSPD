import os


class IgnoreFile:
    sign2ignore_line_in_ignoring_file = "#"
    sign2note_that_system_should_ignore_all_folder = "/"

    description_for_user_in_ignoring_file = f"""{sign2ignore_line_in_ignoring_file} Lines started with '{sign2ignore_line_in_ignoring_file}' is comments - system won't look them
{sign2ignore_line_in_ignoring_file} Put here files that you want to ignore in ssh project delivering process
{sign2ignore_line_in_ignoring_file} System will look files only in local folder that you put in config
{sign2ignore_line_in_ignoring_file} If you want to put ignore all folder - paste '{sign2note_that_system_should_ignore_all_folder}' after dir name
    """

    example_of_default_files_to_ignore = f"""
{sign2ignore_line_in_ignoring_file} For example:
ssh_project_delivery{sign2note_that_system_should_ignore_all_folder}
ssh_project_delivery.py
.git{sign2note_that_system_should_ignore_all_folder}
.gitignore
playground.py
venv{sign2note_that_system_should_ignore_all_folder}
.idea{sign2note_that_system_should_ignore_all_folder}
__pycache__{sign2note_that_system_should_ignore_all_folder}
.DS_Store
README.md
    """

    def __init__(self, ignore_filepath: str, project_path: str):
        ignore_filepath = ignore_filepath.strip()
        if not ignore_filepath.endswith(".ign"):
            ignore_filepath += ".ign"
        try:
            file_lines = self.__init_file_lines(ignore_filepath)
            self.files_to_ignore = self.get_files_skip_comments(file_lines, project_path)
            if len(self.files_to_ignore) == 0:
                raise ValueError("No files to ignore")
        except ValueError:
            file_lines = self.__init_default_file(ignore_filepath)
            self.files_to_ignore = self.get_files_skip_comments(file_lines, project_path)

    def __init_file_lines(self, filepath: str) -> set[str]:
        try:
            with open(filepath, 'r', encoding="UTF-8") as file:
                result = set(file.readlines())
            if len(result) == 0:
                raise ValueError("No lines in file")
        except FileNotFoundError:
            raise ValueError("No lines in file")
        return result

    def __init_default_file(self, filepath: str) -> set[str]:
        with open(filepath, 'w', encoding="UTF-8") as file:
            file.write(self.description_for_user_in_ignoring_file)
        print(f"File '{os.path.join('...', filepath)}' is clean. Do you want to ignore any files?")
        sign2break = "No"
        user_decision = input(f"Enter (to break process) / '{sign2break}' (to continue without ignoring): ")
        if user_decision.strip() != sign2break:
            with open(filepath, 'a+', encoding="UTF-8") as file:
                file.write(self.example_of_default_files_to_ignore)
            os.abort()
        return set()

    def get_files_skip_comments(self, lines_set: set, local_project_path: str) -> set[str]:
        result = set()
        for line in lines_set:
            line = line.strip()

            if line.startswith(self.sign2ignore_line_in_ignoring_file):
                continue

            if line.endswith(self.sign2note_that_system_should_ignore_all_folder):
                for root, dirs, files in os.walk(os.path.join(local_project_path, line)):
                    for file in files:
                        result.add(os.path.join(root, file))
            else:
                result.add(os.path.join(local_project_path, line))
        return result

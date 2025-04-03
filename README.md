# SSPD - ssh/scp project delivery
Tool that help update code in remote `unix` server by uploading files to cloud


### Auto expend project
Lib can:
* make project dir & venv
* install requirements
* create service file
* upload files that was changed or not exists
* control starting and stopping execution
* execute your personal commands
* ...

You also have access to specify lib job by using module `sspd.tasks`


### Quick start
```commandline
pip install -U git+https://github.com/MatveyFilippov/SSPD.git
```

or install old version from [dist](dist)

```python
import sspd

try:
    sspd.tasks.update_remote_code()
finally:
    sspd.close_connections()
```
It will ask you about properties and create `.ini` & `.ign` files


### More examples
To install dev version (or another branch)
```commandline
pip install -U git+https://github.com/MatveyFilippov/SSPD.git@dev
```
SSPD is a rich set of tools that can be used in any way in your program.
```python
import sspd
from enum import Enum
from typing import NoReturn


class Direction(Enum):
    EXIT = 0
    UPDATE_CODE = 1
    DOWNLOAD_LOGS = 2
    STOP_RUNNING = 3
    START_RUNNING = 4
    DELETE_NOT_REQUIRED_DATA = 5

    @classmethod
    def get_direction(cls) -> 'Direction':
        """Get user input and return the selected Direction enum."""
        print("Choose what will be done")
        for direction in cls:
            name = direction.name.replace("_", " ").title()
            print(f" * {name} ({direction.value})")
        try:
            return cls(int(input(": ").strip()))
        except ValueError:
            print("No such variant -> exit")
            return cls.EXIT


def delete_not_required_data():
    """Custom sspd task"""
    sspd.tasks.stop_running_remote_code()
    sspd.tasks.execute_remote_command(
        command=f"{sspd.base.REMOTE_PROJECT_DIR_PATH}/UserCaches clean",
        ignore_error=True
    )
    sspd.tasks.execute_remote_command(
        command=f"mv new.homer old.homer",
        print_request=True, print_response=True,
        in_dir="/homer/datas"
    )
    sspd.tasks.start_running_remote_code()


HANDLERS = {
    Direction.EXIT: lambda: None,
    Direction.UPDATE_CODE: sspd.tasks.update_remote_code,
    Direction.DELETE_NOT_REQUIRED_DATA: delete_not_required_data,
    Direction.START_RUNNING: sspd.tasks.start_running_remote_code,
    Direction.STOP_RUNNING: sspd.tasks.stop_running_remote_code,
    Direction.DOWNLOAD_LOGS: sspd.tasks.download_log_file,
}


def main() -> NoReturn:
    try:
        while True:
            user_decision = Direction.get_direction()
            if user_decision == Direction.EXIT:
                break
            HANDLERS[user_decision]()
            print()
    finally:
        sspd.close_connections()


if __name__ == "__main__":
    main()
```


---
###### Created by homer
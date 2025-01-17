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
pip install git+https://github.com/MatveyFilippov/SSPD.git
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


---
###### Created by homer
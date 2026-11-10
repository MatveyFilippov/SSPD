from enum import StrEnum


class Stage(StrEnum):
    DEV = ".dev"
    ALPHA = "a"
    BETA = "b"
    RELEASE_CANDIDATE = "rc"
    STABLE = ""

    def build_version(self, major: int, minor: int, patch: int, stage_num: int) -> tuple[tuple[int, int, int], str]:
        _version_info = (major, minor, patch)

        if any(type(part) is not int or part < 0 for part in _version_info):
            raise ValueError("Version components must be non-negative integers")

        _version = f"{major}.{minor}.{patch}"

        if __stage__ == Stage.STABLE:
            return _version_info, _version

        if type(stage_num) is not int or stage_num < 1:
            raise ValueError("Stage number must be a positive integer")

        return _version_info, _version + f"{self.value}{stage_num}"


########################################################################################################################
# Edit only this block
########################################################################################################################
__stage__ = Stage.DEV
__major__ = 3
__minor__ = 0
__patch__ = 0
__stage_num__ = 2
########################################################################################################################


__version_info__, __version__ = __stage__.build_version(
    major=__major__,
    minor=__minor__,
    patch=__patch__,
    stage_num=__stage_num__,
)

class _Stages:
    DEV = "dev"
    ALPHA = "a"
    BETA = "b"
    RELEASE_CANDIDATE = "rc"
    STABLE = ""

__version_info__ = (3, 0, 0)
__stage__ = _Stages.DEV
__stage_num__ = 2

_base = ".".join(map(str, __version_info__))
__version__ = f"{_base}{__stage__}{__stage_num__}" if __stage__ else _base

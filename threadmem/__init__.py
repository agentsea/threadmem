from .role import RoleMessage, RoleThread, RoleModel, RoleThreadsModel, RoleThreadModel

__all__ = [
    "RoleMessage",
    "RoleThread",
    "RoleModel",
    "RoleThreadsModel",
    "RoleThreadModel",
]


class Thread(RoleThread):
    """A role based chat thread"""

    pass

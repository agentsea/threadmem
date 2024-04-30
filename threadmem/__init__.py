from .role import RoleMessage, RoleThread, V1Role, V1RoleThread, V1RoleThreads

__all__ = [
    "RoleMessage",
    "RoleThread",
    "V1Role",
    "V1RoleThread",
    "V1RoleThreads",
]


class Thread(RoleThread):
    """A role based chat thread"""

    pass

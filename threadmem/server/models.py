from typing import Dict, List, Optional

from pydantic import BaseModel


class V1Message(BaseModel):
    id: str
    author: str
    text: str
    images: List[str] = []
    private: Optional[bool] = None
    metadata: Optional[dict] = None
    created: float
    thread_id: Optional[str] = None


class V1DeleteThread(BaseModel):
    name: str


class V1Thread(BaseModel):
    owner_id: Optional[str] = None
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: str
    messages: List[V1Message]
    version: Optional[str] = None
    created: float
    updated: float
    remote: Optional[str] = None


class V1Threads(BaseModel):
    threads: List[V1Thread]


class V1UpdateThread(BaseModel):
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None


class V1CreateThread(BaseModel):
    public: bool = False
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: Optional[str] = None


class V1RoleMessage(BaseModel):
    id: str
    role: str
    text: str
    images: List[str] = []
    private: Optional[bool] = None
    metadata: Optional[dict] = None
    created: float
    thread_id: Optional[str] = None


class V1DeleteRole(BaseModel):
    name: str


class V1Role(BaseModel):
    name: str
    user_id: str
    user_name: str
    icon: str
    description: Optional[str] = None


class V1RoleThread(BaseModel):
    owner_id: Optional[str] = None
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: str
    messages: List[V1RoleMessage]
    role_mapping: Dict[str, V1Role] = {}
    version: Optional[str] = None
    created: float
    updated: float
    remote: Optional[str] = None


class V1RoleThreads(BaseModel):
    threads: List[V1RoleThread]


class V1UpdateRoleThread(BaseModel):
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None


class V1CreateRoleThread(BaseModel):
    public: bool = False
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: Optional[str] = None


class V1UserProfile(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    handle: Optional[str] = None
    picture: Optional[str] = None
    created: Optional[int] = None
    updated: Optional[int] = None
    token: Optional[str] = None


class PostMessageModel(BaseModel):
    role: str
    msg: str
    images: List[str] = []

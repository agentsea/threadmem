from pydantic import BaseModel
from typing import List, Optional


class RoleMessageModel(BaseModel):
    id: str
    role: str
    text: str
    images: List[str] = []
    private: Optional[bool] = None
    metadata: Optional[dict] = None
    created: float
    thread_id: str


class RoleThreadModel(BaseModel):
    owner_id: Optional[str] = None
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: str
    messages: List[RoleMessageModel]
    created: float
    updated: float


class RoleThreadsModel(BaseModel):
    threads: List[RoleThreadModel]


class UpdateRoleThreadModel(BaseModel):
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None


class CreateRoleThreadModel(BaseModel):
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
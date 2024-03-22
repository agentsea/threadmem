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

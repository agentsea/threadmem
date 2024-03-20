from pydantic import BaseModel
from typing import List, Optional


class RoleMessageModel(BaseModel):
    role: str
    text: str
    images: List[str] = []
    private: Optional[bool] = None
    created: float
    id: str
    metadata: Optional[dict] = None


class RoleThreadModel(BaseModel):
    owner_id: Optional[str] = None
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: str
    messages: List[RoleMessageModel]

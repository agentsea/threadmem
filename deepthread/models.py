from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RoleMessageModel(BaseModel):
    role: str
    text: str
    images: List[str] = []
    private: Optional[bool] = None
    created: datetime
    id: str
    metadata: Optional[dict] = None


class RoleThreadModel(BaseModel):
    owner_id: Optional[str] = None
    public: bool
    name: Optional[str] = None
    metadata: Optional[dict] = None
    id: str
    messages: List[RoleMessageModel]

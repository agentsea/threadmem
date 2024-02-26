import uuid
import time

from sqlalchemy import Column, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class RoleMessageRecord(Base):
    __tablename__ = "role_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)
    text = Column(String, nullable=False)
    images = Column(String, nullable=True)
    private = Column(Boolean, nullable=False)
    created = Column(Float, default=time.time)
    meta_data = Column(String, nullable=True)
    thread_id = Column(String, ForeignKey("role_threads.id"))


class RoleThreadRecord(Base):
    __tablename__ = "role_threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, nullable=True)
    public = Column(Boolean, default=False)
    name = Column(String, nullable=True)
    meta_data = Column(String, nullable=True)

    messages = relationship("RoleMessageRecord", backref="role_thread")

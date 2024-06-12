import time
import uuid

from sqlalchemy import Boolean, Column, Float, ForeignKey, String
from sqlalchemy.orm import declarative_base, relationship

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
    thread_id = Column(String, ForeignKey("role_threads.id"), nullable=True)


class RoleThreadRecord(Base):
    __tablename__ = "role_threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, nullable=True)
    public = Column(Boolean, default=False)
    name = Column(String, nullable=True)
    role_mapping = Column(String, nullable=True)
    meta_data = Column(String, nullable=True)
    remote = Column(String, nullable=True)
    version = Column(String, nullable=True)
    created = Column(Float, default=time.time)
    updated = Column(Float, default=time.time)

    messages = relationship(
        "RoleMessageRecord",
        primaryjoin="RoleThreadRecord.id==RoleMessageRecord.thread_id",
        order_by="asc(RoleMessageRecord.created)",
    )


class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    author = Column(String, nullable=False)
    text = Column(String, nullable=False)
    images = Column(String, nullable=True)
    private = Column(Boolean, nullable=False)
    created = Column(Float, default=time.time)
    meta_data = Column(String, nullable=True)
    thread_id = Column(
        String, ForeignKey("threads.id"), nullable=True
    )  # Correct foreign key reference


class ThreadRecord(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, nullable=True)
    public = Column(Boolean, default=False)
    name = Column(String, nullable=True)
    role_mapping = Column(String, nullable=True)
    meta_data = Column(String, nullable=True)
    remote = Column(String, nullable=True)
    version = Column(String, nullable=True)
    created = Column(Float, default=time.time)
    updated = Column(Float, default=time.time)

    messages = relationship(
        "MessageRecord",
        primaryjoin="ThreadRecord.id==MessageRecord.thread_id",
        order_by="asc(MessageRecord.created)",
    )

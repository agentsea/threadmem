import uuid
import time

from sqlalchemy import Column, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    private = Column(Boolean, nullable=False)
    created = Column(Float, default=time.time)
    role = Column(String, nullable=True)
    meta_data = Column(String, nullable=True)
    thread_id = Column(String, ForeignKey("threads.id"))


class ThreadRecord(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, nullable=True)
    public = Column(Boolean, default=False)
    name = Column(String, nullable=True)
    participants = Column(String, nullable=True)
    meta_data = Column(String, nullable=True)

    messages = relationship("MessageRecord", backref="thread")

import uuid
import time

from sqlalchemy import Column, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class GPTMessageRecord(Base):
    __tablename__ = "gpt_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)
    text = Column(String, nullable=False)
    images = Column(String, nullable=True)
    private = Column(Boolean, nullable=False)
    created = Column(Float, default=time.time)
    meta_data = Column(String, nullable=True)
    thread_id = Column(String, ForeignKey("gpt_threads.id"))


class GPTThreadRecord(Base):
    __tablename__ = "gpt_threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, nullable=True)
    public = Column(Boolean, default=False)
    name = Column(String, nullable=True)
    meta_data = Column(String, nullable=True)

    messages = relationship("GPTMessageRecord", backref="gpt_thread")

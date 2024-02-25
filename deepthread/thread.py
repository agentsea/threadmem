from dataclasses import dataclass
from typing import List, Optional
import uuid
import time
import json

from deepthread.db.models import MessageRecord, ThreadRecord
from deepthread.db.conn import WithDB


@dataclass
class Message(WithDB):
    """A chat message"""

    user_id: str
    text: str
    private: bool
    created: float = time.time()
    id: str = str(uuid.uuid4())
    role: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        self.save()

    def to_record(self) -> MessageRecord:
        metadata = json.dumps(self.metadata) if self.metadata else None
        return MessageRecord(
            id=self.id,
            user_id=self.user_id,
            text=self.text,
            private=self.private,
            created=self.created,
            role=self.role,
            meta_data=metadata,
        )

    @classmethod
    def from_record(cls, record: MessageRecord) -> "Message":
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None
        obj = cls.__new__(cls)
        obj.id = record.id
        obj.user_id = record.user_id
        obj.text = record.text
        obj.private = record.private
        obj.created = record.created
        obj.role = record.role
        obj.metadata = metadata_dict
        return obj

    def save(self) -> None:
        for db in self.get_db():
            db.merge(self.to_record())
            db.commit()

    @classmethod
    def find(cls, **kwargs) -> List["Message"]:
        for db in cls.get_db():
            records = db.query(MessageRecord).filter_by(**kwargs).all()
            return [cls.from_record(record) for record in records]


class Thread(WithDB):
    """A chat thread"""

    def __init__(
        self,
        owner_id: Optional[str] = None,
        public: bool = False,
        participants: List[str] = [],
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        self._messages: List[Message] = []
        self._owner_id = owner_id
        self._public = public
        self._participants = participants
        self._id = str(uuid.uuid4())
        self._name = name
        self._metadata = metadata

        self.save()

    def post(self, user_id: str, msg: str, private: bool = False) -> None:
        self._messages.append(Message(user_id, msg, private))
        self.save()

    def messages(self, include_private: bool = True) -> List[Message]:
        if include_private:
            return self._messages

        out = []
        for message in self._messages:
            if not message.private:
                out.append(message)

        return out

    def to_record(self) -> ThreadRecord:
        participants = json.dumps(self._participants) if self._participants else None
        metadata = json.dumps(self._metadata) if self._metadata else None
        return ThreadRecord(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            messages=[message.to_record() for message in self._messages],
            participants=participants,
            name=self._name,
            meta_data=metadata,
        )

    @classmethod
    def from_record(cls, record: ThreadRecord) -> "Thread":
        participants = json.loads(record.participants) if record.participants else []
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None
        obj = cls.__new__(cls)
        obj._id = record.id
        obj._owner_id = record.owner_id
        obj._public = record.public
        obj._participants = participants
        obj._name = record.name
        obj._metadata = metadata_dict
        obj._messages = [Message.from_record(msg) for msg in record.messages]
        return obj

    def save(self) -> None:
        for db in self.get_db():
            db.merge(self.to_record())
            db.commit()

    @classmethod
    def find(cls, **kwargs) -> List["Thread"]:
        for db in cls.get_db():
            records = db.query(ThreadRecord).filter_by(**kwargs).all()
            return [cls.from_record(record) for record in records]

    @property
    def owner_id(self) -> str:
        """Get the owner ID of the thread."""
        return self._owner_id

    @property
    def public(self) -> bool:
        """Check if the thread is public."""
        return self._public

    @property
    def participants(self) -> List[str]:
        """Get the list of participant IDs."""
        return self._participants

    @property
    def name(self) -> Optional[str]:
        """Get the name of the thread."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the thread."""
        self._name = value

    @property
    def metadata(self) -> Optional[dict]:
        """Get the metadata of the thread."""
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict) -> None:
        """Set the metadata of the thread."""
        self._metadata = value

    # You might also want to provide a method to add or remove participants
    def add_participant(self, user_id: str) -> None:
        """Add a participant to the thread."""
        if user_id not in self._participants:
            self._participants.append(user_id)

    def remove_participant(self, user_id: str) -> None:
        """Remove a participant from the thread."""
        if user_id in self._participants:
            self._participants.remove(user_id)

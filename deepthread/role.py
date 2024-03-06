from dataclasses import dataclass, field
from typing import List, Optional, Dict
import uuid
import time
import json
from datetime import datetime

from deepthread.db.models import RoleMessageRecord, RoleThreadRecord
from deepthread.db.conn import WithDB
from .models import RoleMessageModel, RoleThreadModel


@dataclass
class RoleMessage(WithDB):
    """An role based style chat message"""

    role: str
    text: str
    images: List[str] = field(default_factory=list)
    private: Optional[bool] = False
    created: float = time.time()
    id: str = str(uuid.uuid4())
    metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        self.save()

    def to_record(self) -> RoleMessageRecord:
        metadata = json.dumps(self.metadata) if self.metadata else None
        images = json.dumps(self.images) if self.images else None
        return RoleMessageRecord(
            id=self.id,
            text=self.text,
            images=images,
            private=self.private,
            created=self.created,
            role=self.role,
            meta_data=metadata,
        )

    @classmethod
    def from_record(cls, record: RoleMessageRecord) -> "RoleMessage":
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None
        images_list = json.loads(record.images) if record.images else None
        obj = cls.__new__(cls)
        obj.id = record.id
        obj.text = record.text
        obj.private = record.private
        obj.created = record.created
        obj.role = record.role
        obj.metadata = metadata_dict
        obj.images = images_list
        return obj

    def save(self) -> None:
        for db in self.get_db():
            db.merge(self.to_record())
            db.commit()

    @classmethod
    def find(cls, **kwargs) -> List["RoleMessage"]:
        for db in cls.get_db():
            records = db.query(RoleMessageRecord).filter_by(**kwargs).all()
            return [cls.from_record(record) for record in records]

    @classmethod
    def from_schema(cls, schema: RoleMessageModel) -> "RoleMessage":
        obj = cls.__new__(cls)
        obj.id = str(schema.id)
        obj.text = schema.text
        obj.images = schema.images
        obj.private = schema.private
        obj.created = schema.created.timestamp()
        obj.role = schema.role
        obj.metadata = schema.metadata
        return obj

    def to_schema(self) -> RoleMessageModel:
        return RoleMessageModel(
            id=self.id,
            role=self.role,
            text=self.text,
            images=self.images,
            private=self.private,
            created=datetime.fromtimestamp(self.created),
            metadata=self.metadata,
        )


class RoleThread(WithDB):
    """A role based chat thread"""

    def __init__(
        self,
        owner_id: Optional[str] = None,
        public: bool = False,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        self._messages: List[RoleMessage] = []
        self._owner_id = owner_id
        self._public = public
        self._id = str(uuid.uuid4())
        self._name = name
        self._metadata = metadata

        self.save()

    def post(
        self,
        role: str,
        msg: str,
        images: List[str] = [],
        private: bool = False,
        metadata: Optional[dict] = None,
    ) -> None:
        self._messages.append(
            RoleMessage(
                role,
                msg,
                images=images,
                private=private,
                metadata=metadata,
            )
        )
        self.save()

    def messages(self, include_private: bool = True) -> List[RoleMessage]:
        if include_private:
            return self._messages

        out = []
        for message in self._messages:
            if not message.private:
                out.append(message)

        return out

    def to_record(self) -> RoleThreadRecord:
        metadata = json.dumps(self._metadata) if self._metadata else None
        return RoleThreadRecord(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            messages=[message.to_record() for message in self._messages],
            name=self._name,
            meta_data=metadata,
        )

    @classmethod
    def from_record(cls, record: RoleThreadRecord) -> "RoleThread":
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None
        obj = cls.__new__(cls)
        obj._id = record.id
        obj._owner_id = record.owner_id
        obj._public = record.public
        obj._name = record.name
        obj._metadata = metadata_dict
        obj._messages = [RoleMessage.from_record(msg) for msg in record.messages]
        return obj

    def save(self) -> None:
        for db in self.get_db():
            db.merge(self.to_record())
            db.commit()

    @classmethod
    def find(cls, **kwargs) -> List["RoleThread"]:
        for db in cls.get_db():
            records = db.query(RoleThreadRecord).filter_by(**kwargs).all()
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

    def to_oai(self, include_private: bool = False) -> Dict[str, List[Dict[str, str]]]:
        """Convert a RoleThread instance into a format compatible with OpenAI chat completions."""
        formatted_messages = []

        # TODO: support images
        for message in self.messages(include_private=include_private):
            formatted_message = {"role": message.role, "content": message.text}
            formatted_messages.append(formatted_message)

        return {"messages": formatted_messages}

    @classmethod
    def from_schema(cls, schema: RoleThreadModel) -> "RoleThread":
        obj = cls.__new__(cls)
        obj._id = str(schema.id)
        obj._owner_id = schema.owner_id
        obj._public = schema.public
        obj._name = schema.name
        obj._metadata = schema.metadata
        obj._messages = [
            RoleMessage.from_schema(msg_schema) for msg_schema in schema.messages
        ]
        return obj

    def to_schema(self) -> RoleThreadModel:
        return RoleThreadModel(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            name=self._name,
            metadata=self._metadata,
            messages=[message.to_schema() for message in self._messages],
        )

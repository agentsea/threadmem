from dataclasses import dataclass, field
from typing import List, Optional, Dict, TypeVar
import uuid
import time
import json
import os
import hashlib

import requests
from sqlalchemy import asc

from threadmem.db.models import RoleMessageRecord, RoleThreadRecord
from threadmem.db.conn import WithDB
from .server.models import (
    RoleMessageModel,
    RoleThreadModel,
    UpdateRoleThreadModel,
    RoleThreadsModel,
)
from .env import HUB_API_KEY_ENV


R = TypeVar("R", bound="RoleThread")


@dataclass
class RoleMessage(WithDB):
    """An role based style chat message"""

    role: str
    text: str
    thread_id: str
    images: List[str] = field(default_factory=list)
    private: Optional[bool] = False
    created: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
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
            thread_id=self.thread_id,
        )

    @classmethod
    def find(cls, **kwargs) -> List["RoleMessage"]:
        for db in cls.get_db():
            records = (
                db.query(RoleMessageRecord)
                .filter_by(**kwargs)
                .order_by(asc(RoleMessageRecord.created))
                .all()
            )
            return [cls.from_record(record) for record in records]

    @classmethod
    def from_record(cls, record: RoleMessageRecord) -> "RoleMessage":
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None
        images_list = json.loads(record.images) if record.images else []
        obj = cls.__new__(cls)
        obj.id = record.id
        obj.text = record.text
        obj.private = record.private
        obj.created = record.created
        obj.role = record.role
        obj.metadata = metadata_dict
        obj.images = images_list
        obj.thread_id = record.thread_id
        return obj

    def save(self) -> None:
        for db in self.get_db():
            record = self.to_record()
            db.merge(record)
            db.commit()

    @classmethod
    def from_schema(cls, schema: RoleMessageModel) -> "RoleMessage":
        obj = cls.__new__(cls)
        obj.id = str(schema.id)
        obj.text = schema.text
        obj.images = schema.images
        obj.private = schema.private
        obj.created = schema.created
        obj.role = schema.role
        obj.metadata = schema.metadata
        obj.thread_id = schema.thread_id
        return obj

    def to_schema(self) -> RoleMessageModel:
        return RoleMessageModel(
            id=self.id,
            role=self.role,
            text=self.text,
            images=self.images,
            private=self.private,
            created=self.created,
            metadata=self.metadata,
            thread_id=self.thread_id,
        )


class RoleThread(WithDB):
    """A role based chat thread"""

    def __init__(
        self,
        owner_id: Optional[str] = None,
        public: bool = False,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
        remote: Optional[str] = None,
        version: Optional[str] = None,
    ) -> None:
        self._messages: List[RoleMessage] = []
        self._owner_id = owner_id
        self._public = public
        self._id = str(uuid.uuid4())
        self._name = name
        self._metadata = metadata
        self._created = time.time()
        self._updated = time.time()
        self._remote = remote
        self._version = version
        if not self._version:
            self._version = self.generate_version_hash()

        self.save()

    def generate_version_hash(self) -> str:
        task_data = json.dumps(self.to_schema().model_dump(), sort_keys=True)
        hash_version = hashlib.sha256(task_data.encode("utf-8")).hexdigest()
        return hash_version

    @property
    def id(self) -> str:
        return self._id

    def post(
        self,
        role: str,
        msg: str,
        images: List[str] = [],
        private: bool = False,
        metadata: Optional[dict] = None,
    ) -> None:
        if self._remote:
            print("\n!posting msg to remote task", self._id)
            try:
                existing_thread = self._remote_request(
                    self._remote,
                    "POST",
                    f"/v1/rolethreads/{self._id}/msg",
                    {"msg": msg, "role": role, "images": images},
                )
                print("\nfound existing thread", existing_thread)

                if existing_thread["version"] != self._version:
                    print(
                        "WARNING: current thread version is different from remote, you could be overriding changes"
                    )
                print("\nrefreshing task...")
                self.refresh()
                print("\nrefreshed task: ", self.__dict__)
                return
            except Exception as e:
                existing_thread = None
                raise e
        else:
            self._messages.append(
                RoleMessage(
                    role,
                    msg,
                    thread_id=self._id,
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
            remote=self._remote,
            created=self._created,
            updated=self._updated,
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
        obj._created = record.created
        obj._updated = record.updated
        obj._remote = record.remote
        obj._messages = [RoleMessage.from_record(msg) for msg in record.messages]
        return obj

    def to_update_schema(self) -> UpdateRoleThreadModel:
        return UpdateRoleThreadModel(
            name=self._name,
            public=self._public,
            metadata=self._metadata,
        )

    def save(self) -> None:
        print("\n!saving thread", self._id)
        # Generate the new version hash
        new_version = self.generate_version_hash()

        if self._remote:
            print("\n!saving remote thread", self._id)
            try:
                existing_thread = self._remote_request(
                    self._remote, "GET", f"/v1/rolethreads/{self._id}"
                )
                print("\nfound existing thread", existing_thread)

                if existing_thread["version"] != self._version:
                    print(
                        "WARNING: current task version is different from remote, you could be overriding changes"
                    )
            except Exception as e:
                existing_thread = None
                raise e
            if existing_thread:
                print("\nupdating existing thread", existing_thread)
                if self._version != new_version:
                    self._version = new_version
                    print(f"Version updated to {self._version}")

                self._remote_request(
                    self._remote,
                    "PUT",
                    f"/v1/rolethreads/{self._id}",
                    json_data=self.to_update_schema().model_dump(),
                )
                print("\nupdated existing thread", self._id)
            else:
                print("\ncreating new thread", self._id)
                if self._version != new_version:
                    self._version = new_version
                    print(f"Version updated to {self._version}")

                self._remote_request(
                    self._remote,
                    "POST",
                    "/v1/rolethreads",
                    json_data=self.to_schema().model_dump(),
                )
                print("\ncreated new thread", self._id)
        else:
            print("\n!saving local db thread", self._id)
            if self._version != new_version:
                self._version = new_version
                print(f"Version updated to {self._version}")

            for db in self.get_db():
                db.merge(self.to_record())
                db.commit()

    @classmethod
    def find(cls, remote: Optional[str] = None, **kwargs) -> List["RoleThread"]:
        if remote:
            print("finding remote tasks for: ", remote, kwargs)
            remote_response = cls._remote_request(
                remote,
                "GET",
                "/v1/rolethreads",
                json_data={**kwargs, "sort": "created_desc"},
            )
            threads = RoleThreadsModel(**remote_response)
            if remote_response is not None:
                out = [cls.from_schema(record) for record in threads.threads]
                for thread in out:
                    thread._remote = remote
                    print("\nreturning task: ", thread.__dict__)
                return out
        else:
            for db in cls.get_db():
                records = (
                    db.query(RoleThreadRecord)
                    .filter_by(**kwargs)
                    .order_by(asc(RoleThreadRecord.created))
                    .all()
                )
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
    def remote(self) -> Optional[str]:
        """Remote status of the thread."""
        return self._remote

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
        obj._created = schema.created
        obj._updated = schema.updated
        return obj

    def to_schema(self) -> RoleThreadModel:
        return RoleThreadModel(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            name=self._name,
            metadata=self._metadata,
            messages=[message.to_schema() for message in self._messages],
            created=self._created,
            updated=self._updated,
        )

    def delete(self) -> None:
        if self._remote:
            self._remote_request(self._remote, "DELETE", f"/v1/rolethreads/{self._id}")
        else:
            for db in self.get_db():
                db.delete(self.to_record())
                db.commit()

    @classmethod
    def _remote_request(
        self,
        addr: str,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
        auth_token: Optional[str] = None,
    ) -> Optional[List[R]]:
        url = f"{addr}{endpoint}"
        headers = {}
        if not auth_token:
            auth_token = os.getenv(HUB_API_KEY_ENV)
            if not auth_token:
                raise Exception(f"Hub API key not found, set ${HUB_API_KEY_ENV}")
        print(f"\n!auth_token: {auth_token}")
        headers["Authorization"] = f"Bearer {auth_token}"
        try:
            if method.upper() == "GET":
                print("\ncalling remote thread GET with url: ", url)
                print("\ncalling remote thread GET with headers: ", headers)
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                print("\ncalling remote thread POST with: ", url, json_data)
                print("\ncalling remote thread POST with headers: ", headers)
                print("\ncalling remote thread POST with data: ", json_data)
                response = requests.post(url, json=json_data, headers=headers)
            elif method.upper() == "PUT":
                print("\ncalling remote thread PUT with: ", url, json_data)
                print("\ncalling remote thread PUT with headers: ", headers)
                print("\ncalling remote thread PUT with data: ", json_data)
                response = requests.put(url, json=json_data, headers=headers)
            elif method.upper() == "DELETE":
                print("\ncalling remote thread DELETE with: ", url)
                print("\ncalling remote thread DELETE with headers: ", headers)
                response = requests.delete(url, headers=headers)
            else:
                return None

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print("HTTP Error:", e)
                print("Status Code:", response.status_code)
                try:
                    print("Response Body:", response.json())
                except ValueError:
                    print("Raw Response:", response.text)
                raise
            # print("\nresponse: ", response.__dict__)
            print("\response.status_code: ", response.status_code)

            try:
                response_json = response.json()
                # print("\nresponse_json: ", response_json)
                return response_json
            except ValueError:
                print("Raw Response:", response.text)
                return None

        except requests.RequestException as e:
            raise e

    def refresh(self, auth_token: Optional[str] = None) -> None:
        print("\n!refreshing thread", self._id)
        if self._remote:
            print("\n!refreshing remote thread", self._id)
            try:

                remote_thread = self._remote_request(
                    self._remote,
                    "GET",
                    f"/v1/rolethreads/{self._id}",
                    auth_token=auth_token,
                )
                print("\nfound remote thread", remote_thread)
                if remote_thread:
                    schema = RoleThreadModel(**remote_thread)
                    self._public = schema.public
                    self._name = schema.name
                    self._metadata = schema.metadata
                    self._messages = [
                        RoleMessage.from_schema(msg_schema)
                        for msg_schema in schema.messages
                    ]
                    self._updated = schema.updated
                    print("\nrefreshed remote thread", self._id)
            except requests.RequestException as e:
                raise e
        else:
            raise ValueError("Refresh is only supported for remote threads")

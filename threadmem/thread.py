import base64
import copy
import hashlib
import json
import mimetypes
import os
import re
import secrets
import string
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar

import requests
from google.cloud import storage
from PIL import Image
from sqlalchemy import asc

from threadmem.db.conn import WithDB
from threadmem.db.models import MessageRecord, ThreadRecord

from .env import HUB_API_KEY_ENV, STORAGE_BUCKET_ENV, STORAGE_SA_JSON_ENV
from .img import convert_images, image_to_b64
from .role import RoleMessage, RoleThread
from .server.models import V1Message, V1Thread, V1Threads, V1UpdateThread

T = TypeVar("T", bound="Thread")


@dataclass
class Message(WithDB):
    """
    A message that supports text, optional images, and metadata.
    It can be marked as private and is associated with a specific thread.
    Each message is uniquely identified by an ID and records the creation time.

    Args:
        author (str): The sender of the message.
        text (str): The text content of the message.
        thread_id (str): The ID of the thread this message belongs to.
        images (List[str]): A list of image URLs associated with the message. Defaults to an empty list.
        private (Optional[bool]): A flag indicating if the message is private. Defaults to False.
        created (float): The timestamp of when the message was created. Defaults to the current time.
        id (str): A unique identifier for the message. Defaults to a UUID4 string.
        metadata (Optional[dict]): Additional metadata associated with the message. Defaults to None.
    """

    author: str
    text: str
    thread_id: Optional[str] = None
    images: List[str] = field(default_factory=list)
    private: Optional[bool] = False
    created: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        self.save()

    def to_record(self) -> MessageRecord:
        """
        Converts the Message instance into a MessageRecord for database storage.

        Returns:
            MessageRecord: An instance of MessageRecord with fields populated from the Message instance.
        """
        metadata = json.dumps(self.metadata) if self.metadata else None
        images = json.dumps(self.images) if self.images else None

        new_imgs = convert_images(self.images)  # type: ignore
        images = json.dumps(new_imgs)

        return MessageRecord(
            id=self.id,
            text=self.text,
            images=images,
            private=self.private,
            created=self.created,
            author=self.author,
            meta_data=metadata,
            thread_id=self.thread_id,
        )

    @classmethod
    def find(cls, **kwargs) -> List["Message"]:
        """
        Finds and returns a list of Message instances based on the provided search criteria.

        This method queries the database for Message records that match the given keyword arguments.
        The results are ordered by the creation time of the messages in ascending order.

        Args:
            **kwargs: Arbitrary keyword arguments that are passed to the filter_by method of the database query.
                      These arguments should correspond to the attributes of the MessageRecord model.

        Examples:
            >>> found_messages = Message.find(author="example_sender")

        Returns:
            List[Message]: A list of Message instances that match the search criteria.
        """
        for db in cls.get_db():
            records = (
                db.query(MessageRecord)
                .filter_by(**kwargs)
                .order_by(asc(MessageRecord.created))
                .all()
            )
            return [cls.authorrecord(record) for record in records]

        raise ValueError("no session")

    @classmethod
    def authorrecord(cls, record: MessageRecord) -> "Message":
        """
        Converts a MessageRecord instance back into a Message instance.

        This method is used to reconstruct a Message object from its stored representation in the database.
        It takes a MessageRecord object, which represents a row in the database, and converts it into a
        Message object by extracting and converting the stored fields.

        Args:
            record (MessageRecord): The database record to convert.

        Returns:
            Message: The reconstructed Message object.
        """
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None  # type: ignore
        images_list = json.loads(record.images) if record.images else []  # type: ignore
        obj = cls.__new__(cls)
        obj.id = record.id  # type: ignore
        obj.text = record.text  # type: ignore
        obj.private = record.private  # type: ignore
        obj.created = record.created  # type: ignore
        obj.author = record.author  # type: ignore
        obj.metadata = metadata_dict
        obj.images = images_list
        obj.thread_id = record.thread_id  # type: ignore
        return obj

    def save(self) -> None:
        """
        Saves the current state of the Message instance to the database.

        This method converts the Message instance into a MessageRecord (the database model representation)
        and merges it with the existing record in the database if it exists, or creates a new record if it does not.
        After merging, it commits the changes to the database to ensure the Message instance is saved.

        Raises:
            SQLAlchemyError: If there is an issue with database connectivity or the merge and commit operations.
        """
        for db in self.get_db():
            record = self.to_record()
            db.merge(record)
            db.commit()

    @classmethod
    def authorv1(cls, schema: V1Message) -> "Message":
        """
        Converts a MessageModel instance into a Message instance.

        This method is used to create a Message object from a MessageModel schema. It takes a MessageModel
        object, which represents a structured input, possibly coming from an API request or another external source,
        and converts it into a Message object by directly mapping the schema fields to the Message object fields.

        Args:
            schema (V1Message): The schema to convert.

        Returns:
            Message: The newly created Message object.
        """
        obj = cls.__new__(cls)
        obj.id = str(schema.id)
        obj.text = schema.text
        obj.images = schema.images
        obj.private = schema.private
        obj.created = schema.created
        obj.author = schema.author
        obj.metadata = schema.metadata
        obj.thread_id = schema.thread_id
        return obj

    def to_v1(self) -> V1Message:
        """
        Converts the current Message instance into a MessageModel.

        This method is used to create a MessageModel object from the current Message instance. It directly maps
        the fields of the Message instance to the corresponding fields in the MessageModel, ensuring that the
        data structure is compatible for serialization or API response purposes.

        Returns:
            MessageModel: The MessageModel object created from the Message instance.
        """
        return V1Message(
            id=self.id,
            author=self.author,
            text=self.text,
            images=self.images,
            private=self.private,
            created=self.created,
            metadata=self.metadata,
            thread_id=self.thread_id,
        )


class Thread(WithDB):
    """
    Represents a chat thread where messages are organized.
    Each thread can be public or private, have a unique owner, and contain metadata
    for additional context. Threads are identified by a unique ID and can be
    versioned for tracking changes over time.
    """

    def __init__(
        self,
        owner_id: Optional[str] = None,
        public: bool = False,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
        remote: Optional[str] = None,
        version: Optional[str] = None,
    ) -> None:
        """
        Initializes a new instance of the Thread class.

        This constructor initializes a chat thread with various attributes including owner ID, visibility,
        name, metadata, remote location, and version. It generates a unique ID for the thread, sets the creation and
        update times to the current time, and if no version is provided, generates a version hash based on the thread's
        schema. Finally, it saves the new thread instance to the database.

        Args:
            owner_id (Optional[str]): The ID of the thread owner. Defaults to None.
            public (bool): A flag indicating whether the thread is public. Defaults to False.
            name (Optional[str]): The name of the thread. Defaults to None.
            metadata (Optional[dict]): A dictionary containing metadata about the thread. Defaults to None.
            remote (Optional[str]): The remote location of the thread, if any. Defaults to None.
            version (Optional[str]): The version of the thread. If not provided, a version hash is generated. Defaults to None.
        """
        self._messages: List[Message] = []
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
        """
        Generates a version hash for the RoleThread instance.

        This method serializes the RoleThread instance into a JSON string, ensuring the keys are sorted to maintain
        consistency. It then encodes the JSON string into bytes and computes a SHA-256 hash of these bytes. The resulting
        hash is used as the version identifier for the RoleThread instance.

        Returns:
            str: A hexadecimal string representing the SHA-256 hash of the serialized RoleThread instance.
        """
        task_data = json.dumps(self.to_v1().model_dump(), sort_keys=True)
        hash_version = hashlib.sha256(task_data.encode("utf-8")).hexdigest()
        return hash_version

    @classmethod
    def authoropenai(cls, msgs: List[dict]) -> "Thread":
        thread = Thread()
        for msg in msgs:
            author = msg["from"]
            content = msg["content"]

            images = []
            text = ""

            if isinstance(content, list):
                for c in content:
                    if c["type"] == "text":
                        text = c["text"]
                    elif c["type"] == "image_url":
                        images.append(c["url"])
            else:
                text = content

            # TODO: ineffiecient
            thread.post(author, text, images)

        return thread

    def add_msg(self, msg: Message) -> None:
        """
        Add a message to the Thread.

        This method allows for posting a message to the Thread, optionally including images,
        marking the message as private, and attaching metadata. If the Thread is marked as remote,
        the message is posted to a remote server. Otherwise, it is stored locally.

        Args:
            msg (Message): The message instance.

        Raises:
            Exception: If an error occurs while posting the message to a remote server.
        """
        if self._remote:
            try:
                self._remote_request(
                    self._remote,
                    "POST",
                    f"/v1/threads/{self._id}/msgs",
                    msg.to_v1().model_dump(),
                )
                self.refresh()
                return
            except Exception as e:
                raise e
        else:
            self._messages.append(msg)
            self.save()

    def post(
        self,
        author: str,
        msg: str,
        images: List[str | Image.Image] = [],
        private: bool = False,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Posts a message to the Thread.

        This method allows for posting a message to the Thread, optionally including images,
        marking the message as private, and attaching metadata. If the Thread is marked as remote,
        the message is posted to a remote server. Otherwise, it is stored locally.

        Args:
            author (str): The sender of the message.
            msg (str): The message text.
            images (List[str | Image.Image], optional): A list of images; accepts URLs, PIL images, local filepaths, or b64 encoded images.
                Defaults to an empty list.
            private (bool, optional): Whether the message is private. Defaults to False.
            metadata (Optional[dict], optional): Additional metadata for the message. Defaults to None.

        Raises:
            Exception: If an error occurs while posting the message to a remote server.
        """
        new_imgs: List[str] = []
        for img in images:
            if isinstance(img, Image.Image):
                new_imgs.append(image_to_b64(img))
            elif isinstance(img, str):
                if img.startswith("data:") or img.startswith("http"):
                    new_imgs.append(img)
                else:
                    loaded_img = Image.open(img)
                    new_imgs.append(image_to_b64(loaded_img))
            else:
                raise ValueError("unnknown image type")

        if self._remote:
            try:
                self._remote_request(
                    self._remote,
                    "POST",
                    f"/v1/threads/{self._id}/msgs",
                    {"msg": msg, "author": author, "images": images},
                )
                self.refresh()
                return
            except Exception as e:
                raise e
        else:
            self._messages.append(
                Message(
                    author=author,
                    text=msg,
                    thread_id=self._id,
                    images=new_imgs,
                    private=private,
                    metadata=metadata,
                )
            )
            self.save()

    def messages(self, include_private: bool = True) -> List[Message]:
        """
        Retrieves a list of messages associated with the Thread.

        This method filters messages based on the `include_private` parameter. If `include_private` is True,
        all messages are returned. If False, only public messages are returned.

        Args:
            include_private (bool, optional): A flag to determine if private messages should be included.
                                               Defaults to True.

        Returns:
            List[Message]: A list of Message instances that match the filter criteria.
        """
        if include_private:
            return self._messages

        out = []
        for message in self._messages:
            if not message.private:
                out.append(message)

        return out

    def to_record(self) -> ThreadRecord:
        """
        Converts the Thread instance into a ThreadRecord for database storage.

        Returns:
            ThreadRecord: An instance of ThreadRecord with fields populated from the Thread instance.
        """
        metadata = json.dumps(self._metadata) if self._metadata else None

        return ThreadRecord(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            messages=[message.to_record() for message in self._messages],
            name=self._name,
            meta_data=metadata,
            remote=self._remote,
            created=self._created,
            updated=self._updated,
            version=self._version,
        )

    @classmethod
    def authorrecord(cls, record: ThreadRecord) -> "Thread":
        """
        Creates an instance of Thread from a ThreadRecord.

        Args:
            record (ThreadRecord): The database record to convert into a Thread instance.

        Returns:
            Thread: An instance of Thread with properties populated from the database record.
        """
        metadata_dict = json.loads(str(record.meta_data)) if record.meta_data else None  # type: ignore

        obj = cls.__new__(cls)
        obj._id = record.id
        obj._owner_id = record.owner_id
        obj._public = record.public
        obj._name = record.name
        obj._metadata = metadata_dict
        obj._created = record.created
        obj._updated = record.updated
        obj._remote = record.remote
        obj._version = record.version
        obj._messages = [Message.authorrecord(msg) for msg in record.messages]
        obj._remote = None
        return obj

    def to_update_schema(self) -> V1UpdateThread:
        """
        Generates an UpdateThreadModel instance with current thread properties.

        This method prepares the data for updating an existing Thread by creating an UpdateThreadModel instance.
        It includes the thread's name, visibility (public or private), and metadata.

        Returns:
            UpdateThreadModel: An instance populated with the current thread's name, visibility, and metadata.
        """
        return V1UpdateThread(
            name=self._name,
            public=self._public,
            metadata=self._metadata,
        )

    def save(self) -> None:
        """
        Saves the Thread instance to the database.

        This method saves the Thread instance to the database.
        If the thread is remote, it sends a request to the remote server to update or create the thread.
        If the thread is local, it saves the thread to the database.
        """
        new_version = self.generate_version_hash()

        if self._remote:
            try:
                existing_thread = self._remote_request(
                    self._remote, "GET", f"/v1/threads/{self._id}"
                )

                if existing_thread["version"] != self._version:  # type: ignore
                    print(
                        "WARNING: current task version is different from remote, you could be overriding changes"
                    )
            except Exception as e:
                existing_thread = None
                raise e
            if existing_thread:
                if self._version != new_version:
                    self._version = new_version
                    print(f"Version updated to {self._version}")

                self._remote_request(
                    self._remote,
                    "PUT",
                    f"/v1/threads/{self._id}",
                    json_data=self.to_update_schema().model_dump(),
                )
            else:
                if self._version != new_version:
                    self._version = new_version

                self._remote_request(
                    self._remote,
                    "POST",
                    "/v1/threads",
                    json_data=self.to_v1().model_dump(),
                )
        else:
            if self._version != new_version:
                self._version = new_version

            for db in self.get_db():
                db.merge(self.to_record())
                db.commit()

    @classmethod
    def find(cls, remote: Optional[str] = None, **kwargs) -> List["Thread"]:
        """
        Finds Thread instances based on various criteria.

        This method retrieves Thread instances based on the provided keyword arguments.
        If a remote server is specified, it sends a request to the remote server to fetch the threads.
        If no remote server is specified, it retrieves the threads from the local database.

        Args:
            remote (Optional[str]): The remote server URL to fetch threads from. Defaults to None.
            **kwargs: Additional keyword arguments for filtering the threads.

        Example:
            >>> remote_url = "http://example.com"
            >>> owner_id = "user123"
            >>> found_threads = Thread.find(remote=remote_url, owner_id=owner_id)
            >>> print(found_threads)
            [Thread(owner_id='user123', public=True, name='Thread Name', ...)]

        Returns:
            List[Thread]: A list of Thread instances that match the filter criteria.
        """
        if remote:
            remote_response = cls._remote_request(
                remote,
                "GET",
                "/v1/threads",
                json_data={**kwargs, "sort": "created_desc"},
            )
            if not remote_response:
                raise ValueError(
                    "expected response from remote request to list threads"
                )
            threads = V1Threads(**remote_response)
            out = [cls.authorv1(record) for record in threads.threads]
            for thread in out:
                thread._remote = remote
            return out
        else:
            for db in cls.get_db():
                records = (
                    db.query(ThreadRecord)
                    .filter_by(**kwargs)
                    .order_by(asc(ThreadRecord.created))
                    .all()
                )
                return [cls.authorrecord(record) for record in records]

            raise Exception("no session")

    @property
    def owner_id(self) -> Optional[str]:
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

    @classmethod
    def authorv1(cls, schema: V1Thread) -> "Thread":
        """
        Creates an instance of Thread from a ThreadModel.
        """
        obj = cls.__new__(cls)
        obj._id = str(schema.id)
        obj._owner_id = schema.owner_id
        obj._public = schema.public
        obj._name = schema.name
        obj._metadata = schema.metadata
        obj._messages = [Message.authorv1(msg_schema) for msg_schema in schema.messages]
        obj._created = schema.created
        obj._updated = schema.updated
        obj._version = schema.version
        obj._remote = schema.remote
        return obj

    def to_v1(self) -> V1Thread:
        """
        Converts the Thread instance into a ThreadModel for API representation.
        """
        return V1Thread(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            name=self._name,
            metadata=self._metadata,
            version=self._version,
            messages=[message.to_v1() for message in self._messages],
            created=self._created,
            updated=self._updated,
            remote=self._remote,
        )

    def delete(self) -> None:
        """
        Deletes the Thread instance from the database.
        """
        if self._remote:
            self._remote_request(self._remote, "DELETE", f"/v1/threads/{self._id}")
        else:
            for db in self.get_db():
                db.delete(self.to_record())
                db.commit()

    @classmethod
    def _remote_request(
        cls,
        addr: str,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
        auth_token: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        url = f"{addr}{endpoint}"
        headers = {}
        if not auth_token:
            auth_token = os.getenv(HUB_API_KEY_ENV)
            if not auth_token:
                raise Exception(f"Hub API key not found, set ${HUB_API_KEY_ENV}")
        headers["Authorization"] = f"Bearer {auth_token}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=json_data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=json_data, headers=headers)
            elif method.upper() == "DELETE":
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

            try:
                response_json = response.json()
                return response_json
            except ValueError:
                print("Raw Response:", response.text)
                return None

        except requests.RequestException as e:
            raise e

    def copy(self) -> "Thread":
        """
        Creates a copy of the current Thread instance with a new unique ID but with identical other attributes.

        Returns:
            Thread: A new Thread instance that is a copy of the current instance with a new unique ID.
        """
        copied_thread = copy.deepcopy(self)
        copied_thread._id = str(uuid.uuid4())
        copied_thread._created = time.time()
        copied_thread._updated = time.time()
        return copied_thread

    def refresh(self, auth_token: Optional[str] = None) -> None:
        """
        Refreshes the Thread instance from the remote server.
        """
        if self._remote:
            try:
                remote_thread = self._remote_request(
                    self._remote,
                    "GET",
                    f"/v1/threads/{self._id}",
                    auth_token=auth_token,
                )
                if remote_thread:
                    schema = V1Thread(**remote_thread)
                    self._public = schema.public
                    self._name = schema.name
                    self._metadata = schema.metadata
                    self._messages = [
                        Message.authorv1(msg_schema) for msg_schema in schema.messages
                    ]
                    self._updated = schema.updated
            except requests.RequestException as e:
                raise e
        else:
            raise ValueError("Refresh is only supported for remote threads")

    def remove_images(self) -> None:
        """Remove all images associated with this thread."""
        for message in self.messages():
            if not message:
                continue

            if message.author == "user":
                if message.images:
                    message.images = []
        return

    def to_role_thread(self, role_mapping: Dict[str, str]) -> RoleThread:
        """
        Converts a Thread instance to a RoleThread instance using the provided role mapping.

        Args:
            thread (Thread): The Thread instance to convert.
            role_mapping (Dict[str, str]): The mapping of roles to be used in the RoleThread.

        Returns:
            RoleThread: The converted RoleThread instance.
        """
        # Convert messages
        role_messages = []
        for message in self.messages():
            role = role_mapping.get(message.author)
            if not role:
                raise ValueError(
                    f"expected author '{message.author}' to be in role mapping"
                )
            role_message = RoleMessage(
                role=role,
                text=message.text,
                thread_id=message.thread_id,
                images=message.images,
                private=message.private,
                created=message.created,
                id=message.id,
                metadata=message.metadata,
            )
            role_messages.append(role_message)

        # Create RoleThread
        role_thread = RoleThread(
            owner_id=self.owner_id,
            public=self.public,
            name=self.name,
            metadata=self.metadata,
            remote=self.remote,
            version=self._version,
        )

        # Add messages to RoleThread
        for role_message in role_messages:
            role_thread.add_msg(role_message)

        return role_thread

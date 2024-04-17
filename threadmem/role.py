from dataclasses import dataclass, field
from typing import List, Optional, Dict, TypeVar, Any
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
    RoleModel,
)
from .env import HUB_API_KEY_ENV


R = TypeVar("R", bound="RoleThread")


@dataclass
class RoleMessage(WithDB):
    """
    A role-based chat message that supports text, optional images, and metadata.
    It can be marked as private and is associated with a specific thread and role.
    Each message is uniquely identified by an ID and records the creation time.

    Fields:

    - **role (str):** The role associated with the message.

    - **text (str):** The text content of the message.

    - **thread_id (str):** The ID of the thread this message belongs to.

    - **images (List[str]):** A list of image URLs associated with the message. Defaults to an empty list.

    - **private (Optional[bool]):** A flag indicating if the message is private. Defaults to False.

    - **created (float):** The timestamp of when the message was created. Defaults to the current time.

    - **id (str):** A unique identifier for the message. Defaults to a UUID4 string.

    - **metadata (Optional[dict]):** Additional metadata associated with the message. Defaults to None.
    """

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
        """
        Converts the RoleMessage instance into a RoleMessageRecord for database storage.

        Returns:
            RoleMessageRecord: An instance of RoleMessageRecord with fields populated from the RoleMessage instance.
        """
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
        """
        Finds and returns a list of RoleMessage instances based on the provided search criteria.

        This method queries the database for RoleMessage records that match the given keyword arguments.
        The results are ordered by the creation time of the messages in ascending order.

        Args:
            **kwargs: Arbitrary keyword arguments that are passed to the filter_by method of the database query.
                      These arguments should correspond to the attributes of the RoleMessageRecord model.

        Examples:
            >>> found_messages = RoleMessage.find(role="example_role")

        Returns:
            List[RoleMessage]: A list of RoleMessage instances that match the search criteria.
        """
        for db in cls.get_db():
            records = (
                db.query(RoleMessageRecord)
                .filter_by(**kwargs)
                .order_by(asc(RoleMessageRecord.created))
                .all()
            )
            return [cls.from_record(record) for record in records]

        raise ValueError("no session")

    @classmethod
    def from_record(cls, record: RoleMessageRecord) -> "RoleMessage":
        """
        Converts a RoleMessageRecord instance back into a RoleMessage instance.

        This method is used to reconstruct a RoleMessage object from its stored representation in the database.
        It takes a RoleMessageRecord object, which represents a row in the database, and converts it into a
        RoleMessage object by extracting and converting the stored fields.

        Args:
            record (RoleMessageRecord): The database record to convert.

        Returns:
            RoleMessage: The reconstructed RoleMessage object.
        """
        metadata_dict = json.loads(record.meta_data) if record.meta_data else None  # type: ignore
        images_list = json.loads(record.images) if record.images else []  # type: ignore
        obj = cls.__new__(cls)
        obj.id = record.id  # type: ignore
        obj.text = record.text  # type: ignore
        obj.private = record.private  # type: ignore
        obj.created = record.created  # type: ignore
        obj.role = record.role  # type: ignore
        obj.metadata = metadata_dict
        obj.images = images_list
        obj.thread_id = record.thread_id  # type: ignore
        return obj

    def save(self) -> None:
        """
        Saves the current state of the RoleMessage instance to the database.

        This method converts the RoleMessage instance into a RoleMessageRecord (the database model representation)
        and merges it with the existing record in the database if it exists, or creates a new record if it does not.
        After merging, it commits the changes to the database to ensure the RoleMessage instance is saved.

        Raises:
            SQLAlchemyError: If there is an issue with database connectivity or the merge and commit operations.
        """
        for db in self.get_db():
            record = self.to_record()
            db.merge(record)
            db.commit()

    @classmethod
    def from_schema(cls, schema: RoleMessageModel) -> "RoleMessage":
        """
        Converts a RoleMessageModel instance into a RoleMessage instance.

        This method is used to create a RoleMessage object from a RoleMessageModel schema. It takes a RoleMessageModel
        object, which represents a structured input, possibly coming from an API request or another external source,
        and converts it into a RoleMessage object by directly mapping the schema fields to the RoleMessage object fields.

        Args:
            schema (RoleMessageModel): The schema to convert.

        Returns:
            RoleMessage: The newly created RoleMessage object.
        """
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
        """
        Converts the current RoleMessage instance into a RoleMessageModel.

        This method is used to create a RoleMessageModel object from the current RoleMessage instance. It directly maps
        the fields of the RoleMessage instance to the corresponding fields in the RoleMessageModel, ensuring that the
        data structure is compatible for serialization or API response purposes.

        Returns:
            RoleMessageModel: The RoleMessageModel object created from the RoleMessage instance.
        """
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
    """
    Represents a role-based chat thread where messages are organized based on roles.
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
        role_mapping: Dict[str, RoleModel] = {},
    ) -> None:
        """
        Initializes a new instance of the RoleThread class.

        This constructor initializes a role-based chat thread with various attributes including owner ID, visibility,
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
        self._role_mapping = role_mapping
        if not self._version:
            self._version = self.generate_version_hash()

        self.save()

    @property
    def role_mapping(self) -> Dict[str, RoleModel]:
        return self._role_mapping

    def add_role(self, role: RoleModel) -> None:
        """
        Adds a new role to the role mapping of the thread.

        If the thread is associated with a remote location, the role is posted to the remote server. If the role already exists in the local role mapping, a ValueError is raised. Otherwise, the role is added to the local role mapping and the thread is saved.

        Args:
            role (RoleModel): The role to be added.

        Raises:
            Exception: If there is an issue posting the role to the remote server.
            ValueError: If the role already exists in the role mapping.
        """
        if self._remote:
            # print("\n!posting msg to remote task", self._id)
            try:
                self._remote_request(
                    self._remote,
                    "POST",
                    f"/v1/rolethreads/{self._id}/roles",
                    role.model_dump(),
                )
                return
            except Exception as e:
                raise e

        if role.name in self._role_mapping:
            raise ValueError(f"Role {role.name} already exists")
        self._role_mapping[role.name] = role
        self.save()

    def remove_role(self, name: str) -> None:
        """
        Removes a role from the role mapping of the thread.

        If the thread is associated with a remote location, the role is removed from the remote server. If the role does not exist in the local role mapping, a ValueError is raised. Otherwise, the role is removed from the local role mapping and the thread is saved.

        Args:
            name (str): The name of the role to be removed.

        Raises:
            Exception: If there is an issue removing the role from the remote server.
            ValueError: If the role does not exist in the role mapping.
        """
        if self._remote:
            # print("\n!removing role from remote", self._id)
            try:
                self._remote_request(
                    self._remote,
                    "DELETE",
                    f"/v1/rolethreads/{self._id}/roles",
                    {"name": name},
                )
                # print("\nrefreshing thread...")
                self.refresh()
                # print("\nrefreshed thread")
                return
            except Exception as e:
                raise e

        if name not in self._role_mapping:
            raise ValueError(f"Role {name} does not exist")
        self._role_mapping.pop(name)
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
        task_data = json.dumps(self.to_schema().model_dump(), sort_keys=True)
        hash_version = hashlib.sha256(task_data.encode("utf-8")).hexdigest()
        return hash_version

    @property
    def id(self) -> str:
        """
        Retrieves the unique identifier of the RoleThread instance.

        This property method returns the unique ID of the RoleThread, which is generated upon the creation of a new RoleThread instance. The ID is a UUID4 string that uniquely identifies the thread among all others.

        Returns:
            str: The unique identifier of the RoleThread instance.
        """
        return self._id

    def post(
        self,
        role: str,
        msg: str,
        images: List[str] = [],
        private: bool = False,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Posts a message to the RoleThread.

        This method allows for posting a message to the RoleThread, optionally including images,
        marking the message as private, and attaching metadata. If the RoleThread is marked as remote,
        the message is posted to a remote server. Otherwise, it is stored locally.

        Args:
            role (str): The role associated with the message.
            msg (str): The message text.
            images (List[str], optional): A list of image URLs. Defaults to an empty list.
            private (bool, optional): Whether the message is private. Defaults to False.
            metadata (Optional[dict], optional): Additional metadata for the message. Defaults to None.

        Raises:
            Exception: If an error occurs while posting the message to a remote server.
        """
        if self._remote:
            # print("\nposting msg to remote task", self._id)
            try:
                self._remote_request(
                    self._remote,
                    "POST",
                    f"/v1/rolethreads/{self._id}/msgs",
                    {"msg": msg, "role": role, "images": images},
                )
                # print("\nrefreshing thread...")
                self.refresh()
                # print("\nrefreshed thread")
                return
            except Exception as e:
                # TODO: this is a local var which doesn't seem to do anything; needs to be fixed
                # existing_thread = None
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
        """
        Retrieves a list of messages associated with the RoleThread.

        This method filters messages based on the `include_private` parameter. If `include_private` is True,
        all messages are returned. If False, only public messages are returned.

        Args:
            include_private (bool, optional): A flag to determine if private messages should be included.
                                               Defaults to True.

        Returns:
            List[RoleMessage]: A list of RoleMessage instances that match the filter criteria.
        """
        if include_private:
            return self._messages

        out = []
        for message in self._messages:
            if not message.private:
                out.append(message)

        return out

    def to_record(self) -> RoleThreadRecord:
        """
        Converts the RoleThread instance into a RoleThreadRecord for database storage.

        Returns:
            RoleThreadRecord: An instance of RoleThreadRecord with fields populated from the RoleThread instance.
        """
        metadata = json.dumps(self._metadata) if self._metadata else None
        role_mapping_dict = {}
        if self._role_mapping:
            for _, role in self._role_mapping.items():
                role_mapping_dict[role.name] = role.model_dump()
        role_mapping = json.dumps(role_mapping_dict)

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
            role_mapping=role_mapping,
            version=self._version,
        )

    @classmethod
    def from_record(cls, record: RoleThreadRecord) -> "RoleThread":
        """
        Creates an instance of RoleThread from a RoleThreadRecord.

        Args:
            record (RoleThreadRecord): The database record to convert into a RoleThread instance.

        Returns:
            RoleThread: An instance of RoleThread with properties populated from the database record.
        """
        metadata_dict = json.loads(str(record.meta_data)) if record.meta_data else None  # type: ignore

        role_mapping_dict = {}
        if record.role_mapping:  # type: ignore
            jdict = json.loads(str(record.role_mapping))
            for role_name, role_dict in jdict.items():
                role_mapping_dict[role_name] = RoleModel(**role_dict)

        obj = cls.__new__(cls)
        obj._id = record.id
        obj._owner_id = record.owner_id
        obj._public = record.public
        obj._name = record.name
        obj._metadata = metadata_dict
        obj._created = record.created
        obj._updated = record.updated
        obj._remote = record.remote
        obj._role_mapping = role_mapping_dict
        obj._version = record.version
        obj._messages = [RoleMessage.from_record(msg) for msg in record.messages]
        obj._remote = None
        return obj

    def to_update_schema(self) -> UpdateRoleThreadModel:
        """
        Generates an UpdateRoleThreadModel instance with current thread properties.

        This method prepares the data for updating an existing RoleThread by creating an UpdateRoleThreadModel instance.
        It includes the thread's name, visibility (public or private), and metadata.

        Returns:
            UpdateRoleThreadModel: An instance populated with the current thread's name, visibility, and metadata.
        """
        return UpdateRoleThreadModel(
            name=self._name,
            public=self._public,
            metadata=self._metadata,
        )

    def save(self) -> None:
        """
        Saves the RoleThread instance to the database.

        This method saves the RoleThread instance to the database.
        If the thread is remote, it sends a request to the remote server to update or create the thread.
        If the thread is local, it saves the thread to the database.
        """
        # print("\nsaving thread", self._id)
        # Generate the new version hash
        new_version = self.generate_version_hash()

        if self._remote:
            # print("\nsaving remote thread", self._id)
            try:
                existing_thread = self._remote_request(
                    self._remote, "GET", f"/v1/rolethreads/{self._id}"
                )
                # print("\nfound existing thread", existing_thread)

                if existing_thread["version"] != self._version:  # type: ignore
                    print(
                        "WARNING: current task version is different from remote, you could be overriding changes"
                    )
            except Exception as e:
                existing_thread = None
                raise e
            if existing_thread:
                # print("\nupdating existing thread", existing_thread)
                if self._version != new_version:
                    self._version = new_version
                    print(f"Version updated to {self._version}")

                self._remote_request(
                    self._remote,
                    "PUT",
                    f"/v1/rolethreads/{self._id}",
                    json_data=self.to_update_schema().model_dump(),
                )
                # print("\nupdated existing thread", self._id)
            else:
                # print("\ncreating new thread", self._id)
                if self._version != new_version:
                    self._version = new_version
                    # print(f"Version updated to {self._version}")

                self._remote_request(
                    self._remote,
                    "POST",
                    "/v1/rolethreads",
                    json_data=self.to_schema().model_dump(),
                )
                # print("\ncreated new thread", self._id)
        else:
            # print("\n!saving local db thread", self._id)
            if self._version != new_version:
                self._version = new_version
                # print(f"Version updated to {self._version}")

            for db in self.get_db():
                db.merge(self.to_record())
                db.commit()

    @classmethod
    def find(cls, remote: Optional[str] = None, **kwargs) -> List["RoleThread"]:
        """
        Finds RoleThread instances based on various criteria.

        This method retrieves RoleThread instances based on the provided keyword arguments.
        If a remote server is specified, it sends a request to the remote server to fetch the threads.
        If no remote server is specified, it retrieves the threads from the local database.

        Args:
            remote (Optional[str]): The remote server URL to fetch threads from. Defaults to None.
            **kwargs: Additional keyword arguments for filtering the threads.

        Example:
            >>> remote_url = "http://example.com"
            >>> owner_id = "user123"
            >>> found_threads = RoleThread.find(remote=remote_url, owner_id=owner_id)
            >>> print(found_threads)
            [RoleThread(owner_id='user123', public=True, name='Thread Name', ...)]

        Returns:
            List[RoleThread]: A list of RoleThread instances that match the filter criteria.
        """
        if remote:
            # print("finding remote tasks for: ", remote, kwargs)
            remote_response = cls._remote_request(
                remote,
                "GET",
                "/v1/rolethreads",
                json_data={**kwargs, "sort": "created_desc"},
            )
            if not remote_response:
                raise ValueError(
                    "expected response from remote request to lest threads"
                )
            threads = RoleThreadsModel(**remote_response)
            out = [cls.from_schema(record) for record in threads.threads]
            for thread in out:
                thread._remote = remote
                # print("\nreturning task: ", thread.__dict__)
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
        """
        Creates an instance of RoleThread from a RoleThreadModel.
        """
        obj = cls.__new__(cls)
        obj._id = str(schema.id)
        obj._owner_id = schema.owner_id
        obj._public = schema.public
        obj._name = schema.name
        obj._metadata = schema.metadata
        obj._messages = [
            RoleMessage.from_schema(msg_schema) for msg_schema in schema.messages
        ]
        obj._role_mapping = schema.role_mapping
        obj._created = schema.created
        obj._updated = schema.updated
        obj._version = schema.version
        obj._remote = schema.remote
        return obj

    def to_schema(self) -> RoleThreadModel:
        """
        Converts the RoleThread instance into a RoleThreadModel for API representation.
        """
        return RoleThreadModel(
            id=self._id,
            owner_id=self._owner_id,
            public=self._public,
            name=self._name,
            metadata=self._metadata,
            version=self._version,
            messages=[message.to_schema() for message in self._messages],
            created=self._created,
            updated=self._updated,
            role_mapping=self._role_mapping,
        )

    def delete(self) -> None:
        """
        Deletes the RoleThread instance from the database.
        """
        if self._remote:
            self._remote_request(self._remote, "DELETE", f"/v1/rolethreads/{self._id}")
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
        # print(f"\n!auth_token: {auth_token}")
        headers["Authorization"] = f"Bearer {auth_token}"
        try:
            if method.upper() == "GET":
                # print("\ncalling remote thread GET with url: ", url)
                # print("\ncalling remote thread GET with headers: ", headers)
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                # print("\ncalling remote thread POST with: ", url, json_data)
                # print("\ncalling remote thread POST with headers: ", headers)
                # print("\ncalling remote thread POST with data: ", json_data)
                response = requests.post(url, json=json_data, headers=headers)
            elif method.upper() == "PUT":
                # print("\ncalling remote thread PUT with: ", url, json_data)
                # print("\ncalling remote thread PUT with headers: ", headers)
                # print("\ncalling remote thread PUT with data: ", json_data)
                response = requests.put(url, json=json_data, headers=headers)
            elif method.upper() == "DELETE":
                # print("\ncalling remote thread DELETE with: ", url)
                # print("\ncalling remote thread DELETE with headers: ", headers)
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
            # print("\response.status_code: ", response.status_code)

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
        """
        Refreshes the RoleThread instance from the remote server.
        """
        # print("\nrefreshing thread", self._id)
        if self._remote:
            # print("\nrefreshing remote thread", self._id)
            try:

                remote_thread = self._remote_request(
                    self._remote,
                    "GET",
                    f"/v1/rolethreads/{self._id}",
                    auth_token=auth_token,
                )
                # print("\nfound remote thread", remote_thread)
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
                    # print("\nrefreshed remote thread", self._id)
            except requests.RequestException as e:
                raise e
        else:
            raise ValueError("Refresh is only supported for remote threads")

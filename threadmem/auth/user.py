from __future__ import annotations
from typing import Optional
import time

from threadmem.server.models import V1UserProfile
from threadmem.db.models import UserRecord
from threadmem.db.conn import WithDB


class User(WithDB):
    email: str
    display_name: str
    picture: str
    created: int
    updated: int

    def __init__(
        self,
        email: str,
        display_name: str,
        picture: str,
    ) -> None:
        found = self.find_one(email)
        if found:
            raise ValueError("user already exists")

        self.email = email
        self.display_name = display_name
        self.picture = picture
        self.created = time.time()
        self.updated = time.time()

        self.save()

    def save(self) -> None:
        for db in self.get_db():
            user_record = UserRecord(
                email=self.email,
                display_name=self.display_name,
                picture=self.picture,
                created=self.created,
                updated=self.updated,
            )
            db.add(user_record)
            db.commit()

    def to_v1_schema(self) -> V1UserProfile:
        return V1UserProfile(
            email=self.email,
            display_name=self.display_name,
            picture=self.picture,
            created=self.created,
            updated=self.updated,
        )

    @classmethod
    def from_v1_schema(cls, schema: V1UserProfile) -> Optional[User]:
        found = cls.find_one(schema.email)
        if found:
            return found

        return cls(schema.email, schema.display_name, schema.picture)

    @classmethod
    def from_state(cls, state: UserRecord) -> User:
        new = cls.__new__(User)
        new.email = state.email
        new.display_name = state.display_name
        new.picture = state.picture
        new.created = state.created
        new.updated = state.updated

        return new

    @classmethod
    def find_one(cls, id: str) -> Optional[User]:
        for db in cls.get_db():
            user_record = db.query(UserRecord).where(UserRecord.email == id).first()
            if not user_record:
                return None
            return cls.from_state(user_record)

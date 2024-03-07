import pytest
from deepthread import RoleMessage
from deepthread.db.models import RoleMessageRecord
from deepthread.db.conn import SessionLocal, get_db

@pytest.fixture
def db():
    db_gen = get_db()
    return next(db_gen)

def test_role_message_creation(db):
    role_message = RoleMessage(role="user", text="Hello, World!")
    role_message.save()
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Hello, World!"
    assert stored_message.role == "user"

def test_role_message_serialization_deserialization(db):
    role_message = RoleMessage(role="admin", text="Test Message", images=["img1.png", "img2.png"], metadata={"key": "value"})
    record = role_message.to_record()
    assert record.meta_data == '{"key": "value"}'
    assert record.images == '["img1.png", "img2.png"]'

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata == {"key": "value"}
    assert deserialized_message.images == ["img1.png", "img2.png"]

def test_role_message_empty_lists_none_values(db):
    role_message = RoleMessage(role="guest", text="Empty Test", images=[], metadata=None)
    record = role_message.to_record()
    assert record.meta_data is None
    assert record.images is None

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata is None
    assert deserialized_message.images is None

def test_role_message_post_init_autosave(db):
    role_message = RoleMessage(role="auto", text="Auto Save Test")
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Auto Save Test"

from random import randint

from threadmem import RoleMessage
from threadmem.db.models import RoleMessageRecord


def generate_random_user() -> str:
    # Generating a string of 3 random numbers between 1 and 100
    random_numbers = "".join([str(randint(1, 100)) for _ in range(3)])
    return f"user{random_numbers}"


def test_role_message_creation():
    random_user = generate_random_user()
    role_message = RoleMessage(role=random_user, text="Hello, World!", thread_id=12345)
    role_message.save()
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Hello, World!"
    assert stored_message.role == random_user


def test_role_message_serialization_deserialization():
    random_admin = generate_random_user()
    role_message = RoleMessage(
        thread_id=12345,
        role=random_admin,
        text="Test Message",
        images=["img1.png", "img2.png"],
        metadata={"key": "value"},
    )
    record = role_message.to_record()
    assert record.meta_data == '{"key": "value"}'
    assert record.images == '["img1.png", "img2.png"]'

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata == {"key": "value"}
    assert deserialized_message.images == ["img1.png", "img2.png"]


def test_role_message_empty_lists_none_values():
    random_guest = generate_random_user()
    role_message = RoleMessage(
        thread_id=12345, role=random_guest, text="Empty Test", images=None, metadata=None
    )
    record = role_message.to_record()
    assert record.meta_data is None, "Metadata should be None"
    assert record.images is None, "Images should be None"

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata is None, "Decerialized Metadata should be None"
    assert deserialized_message.images is None, "Decerialized Images should be None"
    # TODO: we should either change the deserialization to be more consistent or fix this text


def test_role_message_post_init_autosave():
    random_auto = generate_random_user()
    role_message = RoleMessage(thread_id=12345, role=random_auto, text="Auto Save Test")
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Auto Save Test"


def test_multiple_role_message_creation():
    random_user1 = generate_random_user()
    random_user2 = generate_random_user()
    random_admin = generate_random_user()
    messages = [
        RoleMessage(thread_id=12345, role=random_user1, text="First Message"),
        RoleMessage(thread_id=12345, role=random_user2, text="Second Message"),
        RoleMessage(thread_id=12345, role=random_admin, text="Third Message"),
    ]
    for message in messages:
        message.save()

    db = next(messages[0].get_db())
    for message in messages:
        stored_message = db.query(RoleMessageRecord).filter_by(id=message.id).first()
        assert stored_message is not None
        assert stored_message.text == message.text
        assert stored_message.role == message.role


def test_role_message_find_by_role():
    random_user1 = generate_random_user()
    random_admin = generate_random_user()
    role_message1 = RoleMessage(
        thread_id=12345, role=random_user1, text="Find me by role"
    )
    role_message1.save()
    role_message2 = RoleMessage(
        thread_id=12345, role=random_admin, text="You can't find me"
    )
    role_message2.save()

    found_messages = RoleMessage.find(role=random_user1)
    assert len(found_messages) == 1
    assert found_messages[0].text == "Find me by role"


def test_role_message_find_by_text():
    random_user2 = generate_random_user()
    random_admin = generate_random_user()
    role_message1 = RoleMessage(
        thread_id=12345, role=random_user2, text="Find this exact text"
    )
    role_message1.save()
    role_message2 = RoleMessage(
        thread_id=12345, role=random_admin, text="Find this exact text too"
    )
    role_message2.save()

    found_messages = RoleMessage.find(text="Find this exact text")
    assert len(found_messages) > 0
    assert found_messages[-1].role == random_user2


def test_role_message_find_by_id():
    random_user3 = generate_random_user()
    role_message1 = RoleMessage(
        thread_id=12345, role=random_user3, text="Find me by ID"
    )
    role_message1.save()
    search_id = role_message1.id

    found_message = RoleMessage.find(id=search_id)
    assert len(found_message) == 1
    assert found_message[0].text == "Find me by ID"

from random import randint

from deepthread import (
    RoleThread,
    RoleMessage,
)

from deepthread.db.models import RoleMessageRecord


def generate_random_user() -> str:
    # Generating a string of 3 random numbers between 1 and 100
    random_numbers = "".join([str(randint(1, 100)) for _ in range(3)])
    return f"user{random_numbers}"


def test_role_message_creation():
    random_user = generate_random_user()
    role_message = RoleMessage(role=random_user, text="Hello, World!")
    role_message.save()
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Hello, World!"
    assert stored_message.role == random_user


def test_role_message_serialization_deserialization():
    random_admin = generate_random_user()
    role_message = RoleMessage(
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
        role=random_guest, text="Empty Test", images=[], metadata=None
    )
    record = role_message.to_record()
    assert record.meta_data is None
    assert record.images is None

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata is None
    assert deserialized_message.images is None


def test_role_message_post_init_autosave():
    random_auto = generate_random_user()
    role_message = RoleMessage(role=random_auto, text="Auto Save Test")
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Auto Save Test"


def test_multiple_role_message_creation():
    random_user1 = generate_random_user()
    random_user2 = generate_random_user()
    random_admin = generate_random_user()
    messages = [
        RoleMessage(role=random_user1, text="First Message"),
        RoleMessage(role=random_user2, text="Second Message"),
        RoleMessage(role=random_admin, text="Third Message"),
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
    role_message1 = RoleMessage(role=random_user1, text="Find me by role")
    role_message1.save()
    role_message2 = RoleMessage(role=random_admin, text="You can't find me")
    role_message2.save()

    found_messages = RoleMessage.find(role=random_user1)
    assert len(found_messages) == 1
    assert found_messages[0].text == "Find me by role"


def test_role_message_find_by_text():
    random_user2 = generate_random_user()
    random_admin = generate_random_user()
    role_message1 = RoleMessage(role=random_user2, text="Find this exact text")
    role_message1.save()
    role_message2 = RoleMessage(role=random_admin, text="Find this exact text too")
    role_message2.save()

    found_messages = RoleMessage.find(text="Find this exact text")
    assert len(found_messages) > 0
    assert found_messages[-1].role == random_user2


def test_role_message_find_by_id():
    random_user3 = generate_random_user()
    role_message1 = RoleMessage(role=random_user3, text="Find me by ID")
    role_message1.save()
    search_id = role_message1.id

    found_message = RoleMessage.find(id=search_id)
    assert len(found_message) == 1
    assert found_message[0].text == "Find me by ID"


def test_thread_initialization():
    owner_id = generate_random_user()
    public = True
    name = "Test Thread"
    metadata = {"key": "value"}

    thread = RoleThread(owner_id=owner_id, public=public, name=name, metadata=metadata)

    assert thread.owner_id == owner_id
    assert thread.public is public
    assert thread.name == name
    assert thread.metadata == metadata


def test_thread_name_setter():
    thread = RoleThread()
    new_name = "New Thread Name"
    thread.name = new_name
    assert thread.name == new_name


def test_thread_metadata_setter():
    thread = RoleThread()
    new_metadata = {"new_key": "new_value"}
    thread.metadata = new_metadata
    assert thread.metadata == new_metadata


def test_thread_save_and_find():
    owner_id = generate_random_user()
    thread = RoleThread(
        owner_id=owner_id, public=True, name="Test Thread", metadata={"key": "value"}
    )
    thread.save()

    found_threads = RoleThread.find(owner_id=owner_id)
    assert len(found_threads) == 1
    assert found_threads[0].owner_id == owner_id
    assert found_threads[0].name == "Test Thread"


def test_post_message_to_RoleThread():
    owner_id = generate_random_user()
    thread = RoleThread(owner_id=owner_id, public=True, name="Test Thread")
    role = "user"
    message_text = "Hello, Thread!"
    thread.post(role=role, msg=message_text, private=False)

    assert len(thread.messages()) == 1
    assert thread.messages()[0].role == role
    assert thread.messages()[0].text == message_text
    assert thread.messages()[0].private is False


def test_two_users_communication():
    user1_id = generate_random_user()
    user2_id = generate_random_user()
    thread = RoleThread(
        owner_id=user1_id, public=True, name="User Communication Thread"
    )

    # User 1 posts multiple messages
    user1_messages_texts = [
        "Hello from User 1!",
        "How are you?",
        "This is another message from User 1.",
    ]
    for msg_text in user1_messages_texts:
        thread.post(role=user1_id, msg=msg_text, private=False)

    # User 2 posts multiple messages
    user2_messages_texts = [
        "Hello from User 2!",
        "I'm fine, thanks!",
        "Here's another message from User 2.",
    ]
    for msg_text in user2_messages_texts:
        thread.post(role=user2_id, msg=msg_text, private=False)

    thread.save()
    id = thread.id
    thread = RoleThread.find(id=id)[0]

    # Check that all messages are saved correctly
    messages = thread.messages()
    assert len(messages) == 6, "Expected 6 messages in the thread"

    # Check that messages are correctly attributed
    for msg_text in user1_messages_texts:
        assert any(
            message.role == user1_id and message.text == msg_text
            for message in messages
        ), f"User 1's message '{msg_text}' not found"
    for msg_text in user2_messages_texts:
        assert any(
            message.role == user2_id and message.text == msg_text
            for message in messages
        ), f"User 2's message '{msg_text}' not found"

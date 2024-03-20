from random import randint

from threadmem import (
    RoleThread,
    RoleMessage,
)


def generate_random_user() -> str:
    # Generating a string of 3 random numbers between 1 and 100
    random_numbers = "".join([str(randint(1, 100)) for _ in range(3)])
    return f"user{random_numbers}"


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


def test_message_save_and_find():
    role = generate_random_user()
    message = RoleMessage(
        role=role, text="Hello, World!", private=False, metadata={"key": "value"}
    )
    message.save()

    found_messages = RoleMessage.find(role=role)
    assert len(found_messages) == 1
    assert found_messages[0].text == "Hello, World!"


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

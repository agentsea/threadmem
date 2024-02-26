from random import randint

from deepthread import (
    GPTThread,
    GPTMessage,
)


def generate_random_user() -> str:
    # Generating 3 random numbers between 1 and 100
    random_numbers = [randint(1, 100) for _ in range(3)]

    return f"user{random_numbers}"


def test_thread_initialization():
    owner_id = generate_random_user()
    public = True
    name = "Test Thread"
    metadata = {"key": "value"}

    thread = GPTThread(owner_id=owner_id, public=public, name=name, metadata=metadata)

    assert thread.owner_id == owner_id
    assert thread.public is public
    assert thread.name == name
    assert thread.metadata == metadata


def test_thread_name_setter():
    thread = GPTThread()
    new_name = "New Thread Name"
    thread.name = new_name
    assert thread.name == new_name


def test_thread_metadata_setter():
    thread = GPTThread()
    new_metadata = {"new_key": "new_value"}
    thread.metadata = new_metadata
    assert thread.metadata == new_metadata


def test_thread_save_and_find():
    owner_id = generate_random_user()
    thread = GPTThread(
        owner_id=owner_id, public=True, name="Test Thread", metadata={"key": "value"}
    )
    thread.save()

    found_threads = GPTThread.find(owner_id=owner_id)
    assert len(found_threads) == 1
    assert found_threads[0].owner_id == owner_id
    assert found_threads[0].name == "Test Thread"


def test_message_save_and_find():
    user_id = generate_random_user()
    message = GPTMessage(
        role=user_id, text="Hello, World!", private=False, metadata={"key": "value"}
    )
    message.save()

    found_messages = GPTMessage.find(role=user_id)
    assert len(found_messages) == 1
    assert found_messages[0].text == "Hello, World!"


def test_post_message_to_GPTThread():
    owner_id = generate_random_user()
    thread = GPTThread(owner_id=owner_id, public=True, name="Test Thread")
    user_role = "user"
    message_text = "Hello, Thread!"
    thread.post(role=user_role, msg=message_text, private=False)

    assert len(thread.messages()) == 1
    assert thread.messages()[0].role == user_role
    assert thread.messages()[0].text == message_text
    assert thread.messages()[0].private is False

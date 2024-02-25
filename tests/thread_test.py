from agent_threads import (
    Thread,
    Message,
)


def test_thread_initialization():
    owner_id = "user123"
    public = True
    participants = ["user123", "user456"]
    name = "Test Thread"
    metadata = {"key": "value"}

    thread = Thread(owner_id, public, participants, name, metadata)

    assert thread.owner_id == owner_id
    assert thread.public is public
    assert thread.participants == participants
    assert thread.name == name
    assert thread.metadata == metadata


def test_thread_name_setter():
    thread = Thread("user123")
    new_name = "New Thread Name"
    thread.name = new_name
    assert thread.name == new_name


def test_thread_metadata_setter():
    thread = Thread("user123")
    new_metadata = {"new_key": "new_value"}
    thread.metadata = new_metadata
    assert thread.metadata == new_metadata


def test_add_participant():
    thread = Thread("user123", participants=["user123"])
    new_participant = "user789"
    thread.add_participant(new_participant)
    assert new_participant in thread.participants
    # Ensure adding the same participant doesn't duplicate the entry
    thread.add_participant(new_participant)
    assert thread.participants.count(new_participant) == 1


def test_remove_participant():
    initial_participants = ["user123", "user456"]
    thread = Thread("user123", participants=initial_participants)
    thread.remove_participant("user456")
    assert "user456" not in thread.participants
    # Ensure removing a non-existent participant does nothing harmful
    thread.remove_participant("non_existent_user")
    assert len(thread.participants) == 1  # Only "user123" should remain


def test_thread_save_and_find():
    owner_id = "user123"
    thread = Thread(
        owner_id, True, ["user123", "user456"], "Test Thread", {"key": "value"}
    )
    thread.save()

    found_threads = Thread.find(owner_id=owner_id)
    assert len(found_threads) == 1
    assert found_threads[0].owner_id == owner_id
    assert found_threads[0].name == "Test Thread"


def test_message_save_and_find():
    message = Message("user123", "Hello, World!", False, metadata={"key": "value"})
    message.save()

    found_messages = Message.find(user_id="user123")
    assert len(found_messages) == 1
    assert found_messages[0].text == "Hello, World!"

from deepthread import (
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
    Thread(owner_id, True, ["user123", "user456"], "Test Thread", {"key": "value"})

    found_threads = Thread.find(owner_id=owner_id)
    assert len(found_threads) == 1
    assert found_threads[0].owner_id == owner_id
    assert found_threads[0].name == "Test Thread"


def test_message_save_and_find():
    Message("user123", "Hello, World!", False, metadata={"key": "value"})

    found_messages = Message.find(user_id="user123")
    assert len(found_messages) == 1
    assert found_messages[0].text == "Hello, World!"


# def test_post_message_to_thread():
#     # Initialize a thread without messages
#     owner_id = "user123"
#     thread = Thread(owner_id, True, ["user123"], "Test Thread")

#     # Post a message to the thread
#     user_id = "user456"
#     message_text = "Hello, Thread!"
#     thread.post(user_id, message_text, False)

#     # Check if the message is added to the thread's messages
#     assert len(thread.messages()) == 1
#     assert thread.messages()[0].user_id == user_id
#     assert thread.messages()[0].text == message_text
#     assert thread.messages()[0].private is False


# def test_post_multiple_messages_to_thread():
#     # Initialize a thread
#     thread = Thread("user123", True, ["user123"], "Test Thread")

#     # Post multiple messages
#     messages_data = [
#         ("user456", "First message", False),
#         ("user789", "Second message", True),
#     ]

#     for user_id, text, private in messages_data:
#         thread.post(user_id, text, private)

#     # Verify all messages are correctly added
#     assert len(thread.messages()) == len(messages_data)
#     for message, (user_id, text, private) in zip(thread.messages(), messages_data):
#         assert message.user_id == user_id
#         assert message.text == text
#         assert message.private is private


# def test_retrieve_public_messages_only():
#     # Initialize a thread with mixed visibility messages
#     thread = Thread("user123", True, ["user123"], "Test Thread")
#     thread.post("user456", "Public message", False)
#     thread.post("user789", "Private message", True)

#     # Retrieve only public messages
#     public_messages = thread.messages(include_private=False)

#     assert len(public_messages) == 1
#     assert public_messages[0].text == "Public message"
#     assert public_messages[0].private is False


# def test_save_messages_with_thread():
#     # Initialize a thread and add messages
#     thread = Thread(
#         "user123", True, ["user123"], "Test Thread", {"key": "thread value"}
#     )
#     thread.post("user456", "Hello, Thread!", False)
#     thread.save()

#     # Assuming save also persists messages correctly, find thread and check messages
#     found_threads = Thread.find(owner_id="user123")
#     assert len(found_threads) == 1
#     found_thread = found_threads[0]

#     # Reload messages for the found thread to ensure they're retrieved from the database
#     assert len(found_thread.messages()) == 1
#     message = found_thread.messages()[0]
#     assert message.text == "Hello, Thread!"
#     assert message.user_id == "user456"

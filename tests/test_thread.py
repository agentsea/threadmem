from random import randint

from threadmem import RoleThread, RoleMessage


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


def test_thread_save_and_find_by_owner_id():
    owner_id = generate_random_user()
    thread = RoleThread(
        owner_id=owner_id, public=True, name="Test Thread", metadata={"key": "value"}
    )
    thread.save()

    found_threads_by_owner_id = RoleThread.find(owner_id=owner_id)
    assert len(found_threads_by_owner_id) == 1
    assert found_threads_by_owner_id[0].owner_id == owner_id
    assert found_threads_by_owner_id[0].name == "Test Thread"


def test_thread_save_and_find_by_public():
    owner_id = generate_random_user()
    thread = RoleThread(
        owner_id=owner_id, public=True, name="Public Thread", metadata={"key": "value"}
    )
    thread.save()

    found_threads_by_public = RoleThread.find(public=True)
    assert len(found_threads_by_public) > 0
    assert any(thread.public for thread in found_threads_by_public)


def test_thread_save_and_find_by_name():
    owner_id = generate_random_user()
    thread_name = "Unique Thread Name"
    thread = RoleThread(
        owner_id=owner_id, public=True, name=thread_name, metadata={"key": "value"}
    )
    thread.save()

    found_threads_by_name = RoleThread.find(name=thread_name)
    assert len(found_threads_by_name) >= 1
    assert found_threads_by_name[-1].name == thread_name


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


def test_thread_initialization_with_preexisting_messages():
    user_id = generate_random_user()
    preexisting_messages = [
        RoleMessage(thread_id=12345, role=user_id, text="Pre-existing message 1"),
        RoleMessage(thread_id=12345, role=user_id, text="Pre-existing message 2"),
        RoleMessage(thread_id=12345, role=user_id, text="Pre-existing message 3"),
    ]

    thread = RoleThread(
        owner_id=user_id, public=True, name="Pre-existing Messages Thread"
    )

    for message in preexisting_messages:
        thread.post(role=message.role, msg=message.text, private=message.private)

    thread.save()
    id = thread.id
    thread_retrieved = RoleThread.find(id=id)[0]

    assert len(thread_retrieved.messages()) == len(
        preexisting_messages
    ), "The number of messages in the thread does not match the number of pre-existing messages"

    for original_msg, retrieved_msg in zip(
        preexisting_messages, thread_retrieved.messages()
    ):
        assert (
            original_msg.text == retrieved_msg.text
        ), f"Expected message text '{original_msg.text}' but found '{retrieved_msg.text}'"


def test_thread_metadata_setter_and_getter():
    user_id = generate_random_user()
    initial_metadata = {"category": "General", "priority": "High"}
    updated_metadata = {"category": "Specific", "priority": "Low"}

    # Create a thread with initial metadata
    thread = RoleThread(
        owner_id=user_id,
        public=True,
        name="Metadata Test Thread",
        metadata=initial_metadata,
    )
    thread.save()

    # Retrieve the thread and verify initial metadata
    retrieved_thread = RoleThread.find(id=thread.id)[0]
    assert (
        retrieved_thread.metadata == initial_metadata
    ), "Initial metadata does not match"

    # Update the thread metadata
    retrieved_thread.metadata = updated_metadata
    retrieved_thread.save()
    # TODO: we should either save _version in the DB or change this test

    # Retrieve the thread again and verify updated metadata
    updated_thread = RoleThread.find(id=thread.id)[0]
    assert (
        updated_thread.metadata == updated_metadata
    ), "Updated metadata does not match"


def test_thread_message_privacy_filtering():
    user_id = generate_random_user()
    thread = RoleThread(
        owner_id=user_id, public=True, name="Privacy Filter Test Thread"
    )

    # Post both public and private messages
    thread.post(role=user_id, msg="Public Message 1", private=False)
    thread.post(role=user_id, msg="Private Message 1", private=True)
    thread.post(role=user_id, msg="Public Message 2", private=False)

    # Retrieve all messages, including private ones
    all_messages = thread.messages(include_private=True)
    assert len(all_messages) == 3, "Expected 3 messages, including private ones"

    # Retrieve only public messages
    public_messages = thread.messages(include_private=False)
    assert (
        len(public_messages) == 2
    ), "Expected 2 public messages, excluding private ones"

    # Verify that the private message is indeed excluded
    for message in public_messages:
        assert (
            not message.private
        ), "Expected only public messages, but found a private one"


def test_thread_serialization_deserialization():
    owner_id = generate_random_user()
    thread = RoleThread(
        owner_id=owner_id, public=True, name="Serialization Test Thread"
    )
    thread.save()
    messages = [
        RoleMessage(
            thread_id=thread.id, role=owner_id, text="Message 1", private=False
        ),
        RoleMessage(thread_id=thread.id, role=owner_id, text="Message 2", private=True),
    ]
    for message in messages:
        thread.post(role=message.role, msg=message.text, private=message.private)

    # Serialize the thread
    serialized_thread = thread.to_record()
    assert serialized_thread.owner_id == owner_id
    assert serialized_thread.public is True
    assert serialized_thread.name == "Serialization Test Thread"
    assert len(serialized_thread.messages) == 2

    # Deserialize the thread
    deserialized_thread = RoleThread.from_record(serialized_thread)
    assert deserialized_thread.owner_id == owner_id
    assert deserialized_thread.public is True
    assert deserialized_thread.name == "Serialization Test Thread"
    assert len(deserialized_thread.messages()) == 2

    # Verify the messages are correctly associated
    for original, deserialized in zip(messages, deserialized_thread.messages()):
        assert original.text == deserialized.text
        assert original.private == deserialized.private


def test_thread_update_operations():
    owner_id = generate_random_user()
    thread = RoleThread(
        owner_id=owner_id,
        public=True,
        name="Original Thread Name",
        metadata={"original_key": "original_value"},
    )
    thread.save()

    # Update thread properties
    updated_name = "Updated Thread Name"
    updated_metadata = {"updated_key": "updated_value"}
    thread.name = updated_name
    thread.metadata = updated_metadata
    thread.save()

    # Retrieve updated thread from database
    updated_thread = RoleThread.find(id=thread.id)[0]

    # Verify that updates persist correctly
    assert updated_thread.name == updated_name, "Thread name was not updated correctly"
    assert (
        updated_thread.metadata == updated_metadata
    ), "Thread metadata was not updated correctly"


def test_role_thread_to_oai_conversion():
    owner_id = generate_random_user()
    thread = RoleThread(owner_id=owner_id, public=True, name="Test Thread for OAI")

    # Add messages to the thread
    thread.post(role="user", msg="Public message from user", private=False)
    thread.post(role="system", msg="Private system update", private=True)
    thread.post(role="user", msg="Another public message", private=False)

    # Convert to OpenAI format including private messages
    oai_format_with_private = thread.to_openai()
    expected_with_private = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "Public message from user"}],
        },
        {
            "role": "system",
            "content": [{"type": "text", "text": "Private system update"}],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": "Another public message"}],
        },
    ]
    assert (
        oai_format_with_private == expected_with_private
    ), "Conversion including private messages failed"

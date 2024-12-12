from random import randint

import pytest

from threadmem import RoleMessage
from threadmem.db.models import RoleMessageRecord


def generate_random_user() -> str:
    # Generating a string of 3 random numbers between 1 and 100
    random_numbers = "".join([str(randint(1, 100)) for _ in range(3)])
    return f"user{random_numbers}"


def test_role_message_creation():
    random_user = generate_random_user()
    role_message = RoleMessage(
        role=random_user, text="Hello, World!", thread_id="12345"
    )
    role_message.save()
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Hello, World!"  # type: ignore
    assert stored_message.role == random_user  # type: ignore


def test_role_message_serialization_deserialization():
    random_admin = generate_random_user()
    role_message = RoleMessage(
        thread_id="12345",
        role=random_admin,
        text="Test Message",
        images=["./tests/data/img1.webp", "./tests/data/img2.webp"],
        metadata={"key": "value"},
    )
    record = role_message.to_record()
    assert record.meta_data == '{"key": "value"}'  # type: ignore
    print(record.images)

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata == {"key": "value"}
    print(deserialized_message.images)


def test_role_message_empty_lists_none_values():
    random_guest = generate_random_user()
    role_message = RoleMessage(
        thread_id="12345",
        role=random_guest,
        text="Empty Test",
        metadata=None,
    )
    record = role_message.to_record()
    assert record.meta_data is None, "Metadata should be None"

    deserialized_message = RoleMessage.from_record(record)
    assert deserialized_message.metadata is None, "Decerialized Metadata should be None"
    # TODO: we should either change the deserialization to be more consistent or fix this text


def test_role_message_post_init_autosave():
    random_auto = generate_random_user()
    role_message = RoleMessage(
        thread_id="12345", role=random_auto, text="Auto Save Test"
    )
    db = next(role_message.get_db())

    stored_message = db.query(RoleMessageRecord).filter_by(id=role_message.id).first()
    assert stored_message is not None
    assert stored_message.text == "Auto Save Test"  # type: ignore


def test_role_message_to_orign():
    # Test case 1: Text with embedded image tags matching number of images
    role_message = RoleMessage(
        role="user",
        text="Here's the first image: <image> And here's the second one: <image> And some final text",
        images=[
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
        ],
    )

    prompt = role_message.to_orign()
    assert prompt.role == "user"
    assert isinstance(prompt.content, list)
    content = prompt.content
    assert len(content) == 5  # 3 text parts + 2 images

    assert content[0].type == "text"
    assert content[0].text == "Here's the first image:"
    assert content[0].image_url is None

    assert content[1].type == "image_url"
    assert content[1].text is None
    assert (
        content[1].image_url.url  # type: ignore
        == "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"
    )

    # Test case 2: Text with no image tags and no images
    role_message = RoleMessage(
        role="user",
        text="Just some text",
        images=[],
    )

    prompt = role_message.to_orign()
    assert prompt.role == "user"
    assert isinstance(prompt.content, str)
    assert prompt.content == "Just some text"

    # Test case 3: Text with no image tags but with images (images should be appended)
    role_message = RoleMessage(
        role="user",
        text="Just some text",
        images=[
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
        ],
    )

    prompt = role_message.to_orign()
    assert prompt.role == "user"
    assert isinstance(prompt.content, list)
    content = prompt.content
    assert len(content) == 3  # 1 text + 2 images

    assert content[0].type == "text"
    assert content[0].text == "Just some text"

    assert content[1].type == "image_url"
    assert (
        content[1].image_url.url  # type: ignore
        == "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"
    )

    # Test case 6: Empty text with no images
    role_message = RoleMessage(
        role="user",
        text="",
        images=[],
    )

    prompt = role_message.to_orign()
    assert prompt.role == "user"
    assert isinstance(prompt.content, str)  # Changed to expect str instead of list
    assert prompt.content == ""  # Empty string for empty content

    # Test case 4: More image tags than images should raise ValueError
    with pytest.raises(
        ValueError, match="Number of <image> tags .* must match number of images"
    ):
        role_message = RoleMessage(
            role="user",
            text="Image here: <image> Another here: <image> And here: <image>",
            images=["https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"],
        )
        role_message.to_orign()

    # Test case 5: More images than image tags should raise ValueError
    with pytest.raises(
        ValueError, match="Number of <image> tags .* must match number of images"
    ):
        role_message = RoleMessage(
            role="user",
            text="Image here: <image>",
            images=[
                "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
                "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
            ],
        )
        role_message.to_orign()


def test_role_message_to_openai_with_image_tags():
    # Test case 1: Text with embedded image tags matching number of images
    role_message = RoleMessage(
        role="user",
        text="Here's the first image: <image> And here's the second one: <image> And some final text",
        images=[
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
        ],
    )

    openai_format = role_message.to_openai()
    assert openai_format["role"] == "user"
    assert len(openai_format["content"]) == 5  # 3 text parts + 2 images
    assert openai_format["content"][0] == {
        "type": "text",
        "text": "Here's the first image:",
    }
    assert openai_format["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"
        },
    }
    assert openai_format["content"][2] == {
        "type": "text",
        "text": "And here's the second one:",
    }
    assert openai_format["content"][3] == {
        "type": "image_url",
        "image_url": {
            "url": "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"
        },
    }
    assert openai_format["content"][4] == {
        "type": "text",
        "text": "And some final text",
    }

    # Test case 2: Text with no image tags and no images
    role_message = RoleMessage(
        role="user",
        text="Just some text",
        images=[],
    )

    openai_format = role_message.to_openai()
    assert len(openai_format["content"]) == 1  # just text
    assert openai_format["content"][0] == {"type": "text", "text": "Just some text"}

    # Test case 3: Text with no image tags but with images (images should be appended)
    role_message = RoleMessage(
        role="user",
        text="Just some text",
        images=[
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
            "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
        ],
    )

    openai_format = role_message.to_openai()
    assert len(openai_format["content"]) == 3  # 1 text + 2 images
    assert openai_format["content"][0] == {"type": "text", "text": "Just some text"}
    assert openai_format["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"
        },
    }
    assert openai_format["content"][2] == {
        "type": "image_url",
        "image_url": {
            "url": "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"
        },
    }

    # Test case 4: More image tags than images should raise ValueError
    with pytest.raises(
        ValueError, match="Number of <image> tags .* must match number of images"
    ):
        role_message = RoleMessage(
            role="user",
            text="Image here: <image> Another here: <image> And here: <image>",
            images=["https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg"],
        )
        role_message.to_openai()

    # Test case 5: More images than image tags should raise ValueError
    with pytest.raises(
        ValueError, match="Number of <image> tags .* must match number of images"
    ):
        role_message = RoleMessage(
            role="user",
            text="Image here: <image>",
            images=[
                "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
                "https://cdn.britannica.com/51/94151-050-99189B61/Barn.jpg",
            ],
        )
        role_message.to_openai()

    # Test case 6: Empty text with no images
    role_message = RoleMessage(
        role="user",
        text="",
        images=[],
    )

    openai_format = role_message.to_openai()
    assert len(openai_format["content"]) == 0  # empty content


def test_multiple_role_message_creation():
    random_user1 = generate_random_user()
    random_user2 = generate_random_user()
    random_admin = generate_random_user()
    messages = [
        RoleMessage(thread_id="12345", role=random_user1, text="First Message"),
        RoleMessage(thread_id="12345", role=random_user2, text="Second Message"),
        RoleMessage(thread_id="12345", role=random_admin, text="Third Message"),
    ]
    for message in messages:
        message.save()

    db = next(messages[0].get_db())
    for message in messages:
        stored_message = db.query(RoleMessageRecord).filter_by(id=message.id).first()
        assert stored_message is not None
        assert stored_message.text == message.text  # type: ignore
        assert stored_message.role == message.role  # type: ignore


def test_role_message_find_by_role():
    random_user1 = generate_random_user()
    random_admin = generate_random_user()
    role_message1 = RoleMessage(
        thread_id="12345", role=random_user1, text="Find me by role"
    )
    role_message1.save()
    role_message2 = RoleMessage(
        thread_id="12345", role=random_admin, text="You can't find me"
    )
    role_message2.save()

    found_messages = RoleMessage.find(role=random_user1)
    assert len(found_messages) == 1
    assert found_messages[0].text == "Find me by role"


def test_role_message_find_by_text():
    random_user2 = generate_random_user()
    random_admin = generate_random_user()
    role_message1 = RoleMessage(
        thread_id="12345", role=random_user2, text="Find this exact text"
    )
    role_message1.save()
    role_message2 = RoleMessage(
        thread_id="12345", role=random_admin, text="Find this exact text too"
    )
    role_message2.save()

    found_messages = RoleMessage.find(text="Find this exact text")
    assert len(found_messages) > 0
    assert found_messages[-1].role == random_user2


def test_role_message_find_by_id():
    random_user3 = generate_random_user()
    role_message1 = RoleMessage(
        thread_id="12345", role=random_user3, text="Find me by ID"
    )
    role_message1.save()
    search_id = role_message1.id

    found_message = RoleMessage.find(id=search_id)
    assert len(found_message) == 1
    assert found_message[0].text == "Find me by ID"

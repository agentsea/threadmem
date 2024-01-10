from dataclasses import dataclass
from typing import List


@dataclass
class Message:
    """A chat message"""

    user_id: str
    text: str
    private: bool


class Thread:
    """A chat thread"""

    def __init__(
        self, owner_id: str, public: bool = False, participants: List[str] = []
    ) -> None:
        self._messages: List[Message] = []
        self._owner_id = owner_id
        self._public = public
        self._participants = participants

    def post(self, user_id: str, msg: str, private: bool = False) -> None:
        self._messages.append(Message(user_id, msg, private))

    def messages(self, include_private: bool = True) -> List[Message]:
        if include_private:
            return self._messages

        out = []
        for message in self._messages:
            if not message.private:
                out.append(message)

        return out

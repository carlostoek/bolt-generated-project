import logging
from typing import Set, Tuple

logger = logging.getLogger(__name__)

# In-memory storage of messages sent by the bot
_SENT_MESSAGES: Set[Tuple[int, int]] = set()


def store_message(chat_id: int | str, message_id: int) -> None:
    """Store chat_id and message_id for a message sent by the bot."""
    try:
        chat_int = int(chat_id)
    except (TypeError, ValueError):
        logger.error(f"Invalid chat_id provided for store_message: {chat_id}")
        return
    _SENT_MESSAGES.add((chat_int, message_id))
    logger.info(f"Stored message ({chat_int}, {message_id})")


def validate_message(chat_id: int | str, message_id: int) -> bool:
    """Return True if the message pair exists in the store."""
    try:
        chat_int = int(chat_id)
    except (TypeError, ValueError):
        logger.error(f"Invalid chat_id provided for validate_message: {chat_id}")
        return False
    valid = (chat_int, message_id) in _SENT_MESSAGES
    logger.info(
        f"Validation attempt for chat_id={chat_int}, message_id={message_id}: {valid}"
    )
    return valid

"""Tests configuration."""

from unittest.mock import AsyncMock, PropertyMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import Message, User


@pytest.fixture
def test_user_id() -> int:
    """Get test user id for test message.

    Returns:
        Simple int number as user id.
    """
    return 123456


@pytest.fixture
def valid_message_mock(test_user_id: int) -> AsyncMock:
    """Get valid message mock.

    Args:
        test_user_id: id of test user.

    Returns:
        Valid message mock.
    """
    message_mock = AsyncMock(spec=Message)
    message_mock.answer = AsyncMock()
    message_mock.reply = AsyncMock()
    type(message_mock).from_user = PropertyMock(return_value=User(id=test_user_id, is_bot=False, first_name="test"))
    chat_mock = AsyncMock()
    type(chat_mock).type = PropertyMock(return_value=ChatType.PRIVATE)
    type(message_mock).chat = PropertyMock(return_value=chat_mock)
    return message_mock


@pytest.fixture
def invalid_message_mock() -> AsyncMock:
    """Get invalid message mock.

    Returns:
        Invalid message mock.
    """
    message_mock = AsyncMock(spec=Message)
    message_mock.answer = AsyncMock()
    message_mock.reply = AsyncMock()
    type(message_mock).from_user = PropertyMock(return_value=None)
    chat_mock = AsyncMock()
    type(chat_mock).type = PropertyMock(return_value=ChatType.GROUP)
    type(message_mock).chat = PropertyMock(return_value=chat_mock)
    return message_mock

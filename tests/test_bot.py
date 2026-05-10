"""Test bot actions."""
from logging import Logger

from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from aiogram.types import ErrorEvent, ReplyKeyboardMarkup, Update
from pytest_mock import MockType, MockerFixture

from bot import build_keyboard, default_handler, get_user_id, handle_errors
from config import DEFAULT_PHRASES, Buttons
from utils.types import UserStatus


def test_build_keyboard() -> None:
    """Test keyboard creation."""
    test_data: tuple[tuple[UserStatus, Buttons], ...] = (
        # not registered case
        ({"registered": False, "enabled": False, "has_token": False}, Buttons.REGISTER_TEXT),
        # registered and enabled case
        ({"registered": True, "enabled": True, "has_token": True}, Buttons.STOP_TEXT),
        # registered but not enabled case
        ({"registered": True, "enabled": False, "has_token": True}, Buttons.NOTIFY_TEXT),
    )
    for status, button in test_data:
        keyboard = build_keyboard(status)
        assert isinstance(keyboard, ReplyKeyboardMarkup)
        assert keyboard.keyboard[0][0].text == button


@pytest.mark.asyncio
async def test_get_user_id(valid_message_mock: AsyncMock, invalid_message_mock: AsyncMock, test_user_id: int) -> None:
    """Get user from message.

    Args:
        valid_message_mock: mock for valid telegram message.
        invalid_message_mock: mock for invalid telegram message.
        test_user_id: test user id.
    """
    # test user
    valid_answer_mock: AsyncMock = valid_message_mock.answer
    user_id = await get_user_id(valid_message_mock)
    assert user_id == test_user_id, "Wrong user id received"
    valid_answer_mock.assert_not_called()
    # test no user
    invalid_answer_mock: AsyncMock = invalid_message_mock.answer
    user_id = await get_user_id(invalid_message_mock)
    assert user_id is None, "Extra user id received"
    invalid_answer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_handle_errors_unknown(mocker: MockerFixture, ) -> None:
    """Test default message handler during handling unknown error.

    Args:
        valid_message_mock: mock for valid telegram message.
    """
    mocker.patch.object(Logger, 'info')
    mocker.patch.object(Logger, 'warning')
    event = ErrorEvent(update=Update(update_id=123456), exception=Exception("Test"))
    value = await handle_errors(event)
    assert value is False, "Successfully handled unknown error"

@pytest.mark.asyncio
async def test_handle_errors_unknown(mocker: MockerFixture, ) -> None:
    """Test default message handler during handling forbidden error with no message.

    Args:
        valid_message_mock: mock for valid telegram message.
    """
    mocker.patch.object(Logger, 'info')
    mocker.patch.object(Logger, 'warning')
    event = ErrorEvent(
        update=Update(update_id=123456),
        exception=TelegramForbiddenError(method=SendMessage(chat_id=123456, text="test"), message="test"),
    )
    value = await handle_errors(event)
    assert value is False, "Successfully handled forbidden error without message"

@pytest.mark.asyncio
async def test_handle_errors_unknown(mocker: MockerFixture, valid_message_mock: AsyncMock) -> None:
    """Test default message handler during handling forbidden error with message.

    Args:
        valid_message_mock: mock for valid telegram message.
    """
    mocker.patch.object(Logger, 'info')
    mocker.patch.object(Logger, 'warning')
    event = ErrorEvent(
        update=Update(update_id=123456, message=valid_message_mock),
        exception=TelegramForbiddenError(method=SendMessage(chat_id=123456, text="test"), message="test"),
    )
    value = await handle_errors(event)
    assert value is True, "Cannot handle forbidden error with message"


@pytest.mark.asyncio
async def test_default_handler(valid_message_mock: AsyncMock) -> None:
    """Test default message handler.

    Args:
        valid_message_mock: mock for valid telegram message.
    """
    await default_handler(message=valid_message_mock)
    reply_mock: MockType = valid_message_mock.reply
    reply_mock.assert_called_once()
    assert (message := reply_mock.call_args_list[0].args[0]) in DEFAULT_PHRASES, f"Not valid message {message}"

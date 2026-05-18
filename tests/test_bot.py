"""Test bot actions."""

from logging import Logger
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from aiogram.types import ErrorEvent, ReplyKeyboardMarkup, Update
from pytest_mock import MockerFixture, MockType

import bot
from bot import build_keyboard, default_handler, get_user_id, handle_errors, help_handler, main
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
async def test_register_valid(mocker: MockerFixture, valid_message_mock: AsyncMock, test_user_id: int) -> None:
    """Test registration start."""
    mocker.patch("bot.get_user_id", return_value=test_user_id)
    db_mock = mocker.patch("bot.db")
    db_mock.get_user_status = AsyncMock()
    db_mock.get_user_status.return_value = {"registered": False, "enabled": False, "has_token": False}

    state_mock = AsyncMock()
    state_mock.set_state = AsyncMock()

    await bot.register(valid_message_mock, state_mock)

    state_mock.set_state.assert_awaited_once()
    valid_message_mock.answer.assert_called_once()
    # Проверяем, что ForceReply используется
    call_args = valid_message_mock.answer.call_args[1]
    assert "reply_markup" in call_args


@pytest.mark.asyncio
async def test_register_invalid(mocker: MockerFixture, invalid_message_mock: AsyncMock, test_user_id: int) -> None:
    """Test registration start."""
    mocker.patch("bot.get_user_id", return_value=None)
    db_mock = mocker.patch("bot.db")
    db_mock.get_user_status = AsyncMock()
    db_mock.get_user_status.return_value = {"registered": False, "enabled": False, "has_token": False}

    state_mock = AsyncMock()
    state_mock.set_state = AsyncMock()

    await bot.register(invalid_message_mock, state_mock)

    state_mock.set_state.assert_not_awaited()
    invalid_message_mock.answer.assert_not_called()


@pytest.mark.asyncio
async def test_help_handler(mocker: MockerFixture, valid_message_mock: AsyncMock) -> None:
    """Test help information for user.

    Args:
        mocker: fixture to mock logger.
        valid_message_mock: mock for valid telegram message.
    """
    start_mock = mocker.patch.object(bot, "start")
    await help_handler(valid_message_mock)
    start_mock.assert_called_once()


@pytest.mark.asyncio
async def test_handle_errors_unknown(mocker: MockerFixture) -> None:
    """Test default message handler during handling unknown error.

    Args:
        mocker: fixture to mock logger.
    """
    mocker.patch.object(Logger, "info")
    mocker.patch.object(Logger, "warning")
    event = ErrorEvent(update=Update(update_id=123456), exception=Exception("Test"))
    value = await handle_errors(event)
    assert value is False, "Successfully handled unknown error"


@pytest.mark.asyncio
async def test_handle_errors_no_message(mocker: MockerFixture) -> None:
    """Test default message handler during handling forbidden error with no message.

    Args:
        mocker: fixture to mock logger.
    """
    mocker.patch.object(Logger, "info")
    mocker.patch.object(Logger, "warning")
    event = ErrorEvent(
        update=Update(update_id=123456),
        exception=TelegramForbiddenError(method=SendMessage(chat_id=123456, text="test"), message="test"),
    )
    value = await handle_errors(event)
    assert value is False, "Successfully handled forbidden error without message"


@pytest.mark.asyncio
async def test_handle_errors_with_message(mocker: MockerFixture, valid_message_mock: AsyncMock) -> None:
    """Test default message handler during handling forbidden error with message.

    Args:
        mocker: fixture to mock logger.
        valid_message_mock: mock for valid telegram message.
    """
    mocker.patch.object(Logger, "info")
    mocker.patch.object(Logger, "warning")
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


@pytest.mark.asyncio
async def test_main(mocker: MockerFixture) -> None:
    """Test main entry point."""
    create_users_mock = mocker.patch("utils.db.db.create_users")
    bot_mock = AsyncMock()
    bot_constructor = mocker.patch("bot.Bot", return_value=bot_mock)
    dispatcher_instance = AsyncMock()
    dispatcher_instance.start_polling = AsyncMock()
    dispatcher_constructor = mocker.patch("bot.Dispatcher", return_value=dispatcher_instance)
    dispatcher_instance.include_router = Mock()
    dispatcher_instance.message = AsyncMock()
    dispatcher_instance.message.middleware = Mock()
    dispatcher_instance.startup = Mock()
    dispatcher_instance.shutdown = Mock()

    await main()

    create_users_mock.assert_called_once()
    bot_constructor.assert_called_once()
    dispatcher_constructor.assert_called_once()
    dispatcher_instance.include_router.assert_called_once()
    assert dispatcher_instance.message.middleware.call_count == 2
    dispatcher_instance.startup.register.assert_called_once()
    dispatcher_instance.shutdown.register.assert_called_once()
    dispatcher_instance.start_polling.assert_awaited_once_with(bot_mock)

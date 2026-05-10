"""Test bot middlewares."""

from unittest.mock import AsyncMock

import pytest
from aiogram.types import TelegramObject
from pytest_mock import MockerFixture, MockType

from utils.middlewares import LogHandlers, ValidateChatType


@pytest.mark.asyncio
async def test_log_handlers(mocker: MockerFixture) -> None:
    """Test logging middleware.

    Args:
        mocker: fixture for mocking middleware logger.
    """
    logger = mocker.patch("utils.middlewares.logger")
    debug_mock: MockType = logger.debug
    error_mock: MockType = logger.error
    middleware = LogHandlers()
    handler = AsyncMock(return_value="result")
    event = TelegramObject()
    data = {"key": "value"}
    result = await middleware(handler, event, data)
    assert result == "result"
    debug_mock.assert_called_once()
    assert "Call handler" in logger.debug.call_args[0][0]

    class TestError(Exception):
        """Test error."""

        ...

    handler = AsyncMock(side_effect=TestError("test error"))
    with pytest.raises(TestError):
        await middleware(handler, event, data)
    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_validate_chat_type_valid(invalid_message_mock: AsyncMock) -> None:
    """Test valid message handling.

    Args:
        invalid_message_mock: mock for invalid message.
    """
    middleware = ValidateChatType()
    handler = AsyncMock(return_value="result")
    data = {"key": "value"}
    invalid_answer_mock: AsyncMock = invalid_message_mock.answer
    await middleware(handler, invalid_message_mock, data)
    invalid_answer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_validate_chat_type(valid_message_mock: AsyncMock) -> None:
    """Test invalid message handling.

    Args:
        valid_message_mock: mock for valid message.
    """
    middleware = ValidateChatType()
    handler = AsyncMock(return_value="result")
    data = {"key": "value"}
    valid_answer_mock: AsyncMock = valid_message_mock.answer
    await middleware(handler, valid_message_mock, data)
    valid_answer_mock.assert_not_called()

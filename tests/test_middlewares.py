"""Test bot middlewares."""

from unittest.mock import AsyncMock

import pytest
from aiogram.types import TelegramObject
from pytest_mock import MockerFixture, MockType

from utils.middlewares import LogHandlers


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
    handler = AsyncMock(side_effect=ValueError("test error"))
    with pytest.raises(ValueError):
        await middleware(handler, event, data)
    error_mock.assert_called_once()

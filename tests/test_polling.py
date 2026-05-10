"""Test practicum endpoint polling."""

import asyncio
from logging import Logger
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.utils.formatting import Bold, Text
from httpx import AsyncClient, Request, Response
from pytest_mock import MockerFixture

import utils.polling
from utils.db import DB
from utils.polling import get_api_answer, get_message_text, poll_practicum_updates, send_notification
from utils.types import HWItem, HWResponse


@pytest.mark.asyncio
async def test_get_api_answer(mocker: MockerFixture) -> None:
    """Test API answer parsing.

    Args:
        mocker: fixture to mock methods and functions.
    """
    session_get = mocker.patch.object(AsyncClient, "get")

    json_value: HWResponse = {
        "current_date": 123456789,
        "homeworks": [
            {
                "id": 123,
                "status": "finished",
                "date_updated": "test",
                "homework_name": "test",
                "lesson_name": "test",
                "reviewer_comment": "test",
            },
        ],
    }

    session_get.return_value = Response(200, json=json_value, request=Request(method="get", url="test"))

    return_value = await get_api_answer(session=AsyncClient(), token="test", from_timestamp=0)
    assert return_value == json_value["homeworks"]

    class TestError(Exception):
        """Test exception."""

    logger_error = mocker.patch.object(Logger, "error")
    session_get.side_effect = TestError("Some exception")

    with pytest.raises(TestError):
        await get_api_answer(session=AsyncClient(), token="test", from_timestamp=0)

    logger_error.assert_called_once()


def test_get_message_text() -> None:
    """Test that message text is formatted."""
    hw_item: HWItem = {
        "id": 123,
        "status": "finished",
        "date_updated": "2003-02-01T04:05:06Z",
        "homework_name": "homework name",
        "lesson_name": "lesson name",
        "reviewer_comment": "review comment",
    }
    message = get_message_text(hw_item)
    ["01.02.2003 04:05:06" if key == "date_updated" else value for key, value in hw_item.items()]
    payload = message.as_kwargs()
    assert isinstance(message, Text)
    assert (missing_keys := [key for key, value in hw_item.items() if str(value) not in payload["text"]]), (
        f"Missing keys: {missing_keys}"
    )


@pytest.mark.asyncio
async def test_send_notification(mocker: MockerFixture) -> None:
    """Test send_notification error handling.

    Args:
        mocker: fixture to mock methods and functions.
    """
    bot = AsyncMock(spec=Bot)

    class TestError(Exception):
        """Test error."""

        ...

    bot.send_message.side_effect = TestError("boom")
    logger_error = mocker.patch.object(Logger, "error")
    for text in ("test", Text(Bold("test"))):
        logger_error.reset_mock()
        with pytest.raises(TestError):
            await send_notification(bot, chat_id=777, text=text)
        logger_error.assert_called_once()


@pytest.mark.asyncio
async def test_poll_practicum_updates_no_homeworks(mocker: MockerFixture) -> None:
    """Test polling loop when there are no updates.

    Args:
        mocker: fixture to mock methods and functions.
    """
    bot = AsyncMock(spec=Bot)
    mocker.patch.object(
        DB,
        "get_active_users",
        new=AsyncMock(return_value=[{"user_id": 1, "practicum_token": "token", "last_timestamp": 0}]),
    )
    mocker.patch.object(utils.polling, "get_api_answer", new=AsyncMock(return_value=[]))
    send_mock = mocker.patch.object(utils.polling, "send_notification", new=AsyncMock())
    update_mock = mocker.patch.object(DB, "update_last_timestamp", new=AsyncMock())
    mocker.patch.object(  # break loop
        asyncio,
        "sleep",
        new=AsyncMock(side_effect=StopAsyncIteration),
    )
    with pytest.raises(StopAsyncIteration):
        await poll_practicum_updates(bot)
    send_mock.assert_not_awaited()
    update_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_poll_practicum_updates_sends_notifications(mocker: MockerFixture) -> None:
    """Test polling loop with updates.

    Args:
        mocker: fixture to mock methods and functions.
    """
    bot = AsyncMock(spec=Bot)
    mocker.patch.object(
        DB,
        "get_active_users",
        new=AsyncMock(return_value=[{"user_id": 1, "practicum_token": "token", "last_timestamp": 0}]),
    )
    mocker.patch.object(Logger, "info")
    homeworks: list[HWItem] = [
        {
            "id": 1,
            "status": "finished",
            "date_updated": "2003-02-01T04:05:06Z",
            "homework_name": "HW 1",
            "lesson_name": "Lesson 1",
            "reviewer_comment": "Nice",
        },
        {
            "id": 2,
            "status": "rejected",
            "date_updated": "2003-02-01T04:05:06Z",
            "homework_name": "HW 2",
            "lesson_name": "Lesson 2",
            "reviewer_comment": "Fix it",
        },
    ]
    mocker.patch.object(utils.polling, "get_api_answer", new=AsyncMock(return_value=homeworks))
    send_mock = mocker.patch.object(utils.polling, "send_notification", new=AsyncMock())
    update_mock = mocker.patch.object(DB, "update_last_timestamp", new=AsyncMock())
    mocker.patch.object(  # break loop
        asyncio,
        "sleep",
        new=AsyncMock(side_effect=StopAsyncIteration),
    )

    with pytest.raises(StopAsyncIteration):
        await poll_practicum_updates(bot)

    assert send_mock.await_count == 2
    update_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_practicum_updates_user_error(mocker: MockerFixture) -> None:
    """Test user-level exception handling in polling loop.

    Args:
        mocker: fixture to mock methods and functions.
    """
    bot = AsyncMock(spec=Bot)

    mocker.patch.object(
        DB,
        "get_active_users",
        new=AsyncMock(return_value=[{"user_id": 1, "practicum_token": "token", "last_timestamp": 0}]),
    )
    mocker.patch("utils.polling.get_api_answer", new=AsyncMock(side_effect=Exception("api boom")))
    logger_exception = mocker.patch("utils.polling.logger.exception")
    mocker.patch("utils.polling.asyncio.sleep", new=AsyncMock(side_effect=StopAsyncIteration))

    with pytest.raises(StopAsyncIteration):
        await poll_practicum_updates(bot)

    logger_exception.assert_called_once()


@pytest.mark.asyncio
async def test_poll_practicum_updates_outer_error(mocker: MockerFixture) -> None:
    """Test outer loop exception handling in polling loop.

    Args:
        mocker: fixture to mock methods and functions.
    """
    bot = AsyncMock(spec=Bot)

    mocker.patch.object(DB, "get_active_users", new=AsyncMock(side_effect=Exception("db boom")))
    logger_exception = mocker.patch.object(Logger, "exception")
    mocker.patch("utils.polling.asyncio.sleep", new=AsyncMock(side_effect=StopAsyncIteration))

    with pytest.raises(StopAsyncIteration):
        await poll_practicum_updates(bot)

    logger_exception.assert_called_once()

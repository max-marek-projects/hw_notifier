"""Practicum api polling."""

import asyncio
import time
from datetime import datetime

import httpx
from aiogram import Bot
from aiogram.utils.formatting import Bold, Code, Text
from pydantic import TypeAdapter

from config import DateFormats, Urls, config
from logger import logger
from utils.db import db

from .types import HWItem, HWResponse


async def get_api_answer(session: httpx.AsyncClient, token: str, from_timestamp: int) -> list[HWItem]:
    """Fetch homework statuses from API.

    Args:
        session: session to get response with.
        token: authentication token.
        from_timestamp: timestamp to get homeworks starting with.

    Returns:
        List of all new homework statuses.
    """
    try:
        session.headers["Authorization"] = f"OAuth {token}"
        response = await session.get(Urls.PRACTICUM_ENDPOINT, params={"from_date": from_timestamp})
        response.raise_for_status()
        return TypeAdapter(HWResponse).validate_python(response.json())["homeworks"]
    except Exception as ex:
        logger.error(f"API request failed: {ex}")
        raise


def get_message_text(homework: HWItem) -> Text:
    """Format status message.

    Args:
        homework: single homework data.

    Returns:
        Formatted text answer.
    """
    pretty_date = datetime.strptime(homework["date_updated"], DateFormats.PRACTICUM).strftime(DateFormats.USER_FRIENDLY)

    return Text(
        Bold("Update"),
        "\n",
        Bold("- Homework: "),
        Code(str(homework["homework_name"])),
        " (id ",
        Code(str(homework["id"])),
        ")\n",
        Bold("- Lesson: "),
        Code(str(homework["lesson_name"])),
        "\n",
        Bold("- New status: "),
        Code(str(homework["status"])),
        "\n",
        Bold("- At: "),
        pretty_date,
        "\n",
        Bold("- Comment: "),
        Code(str(homework["reviewer_comment"])),
    )


async def send_notification(bot: Bot, chat_id: int, text: str | Text) -> None:
    """Send message to user.

    Args:
        bot: telegram bot.
        chat_id: telegram chat id.
        text: message text.
    """
    try:
        if isinstance(text, Text):
            await bot.send_message(chat_id=chat_id, **text.as_kwargs())
        else:
            await bot.send_message(chat_id=chat_id, text=text)
    except Exception as ex:
        logger.error(f"Failed to send message to {chat_id}: {ex}")
        raise


async def poll_practicum_updates(bot: Bot) -> None:
    """Background task: periodically check for updates for all active users.

    Args:
        bot: telegram bot.
    """
    while True:
        try:
            active_users = await db.get_active_users()
            for user in active_users:
                user_id = user["user_id"]
                current_ts = int(time.time())
                try:
                    async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as session:
                        homeworks = await get_api_answer(
                            session,
                            user["practicum_token"],
                            user.get("last_timestamp", 0),
                        )
                        if not homeworks:
                            continue
                        for hw in homeworks:
                            await send_notification(bot, user_id, get_message_text(hw))
                        await db.update_last_timestamp(user_id, timestamp=current_ts)
                        logger.info(f"Notified user {user_id} about {len(homeworks)} updates")
                except Exception as e:
                    logger.exception(f"Error polling for user {user_id}: {e}")

        except Exception:
            logger.exception("Error in main polling loop")
        finally:
            await asyncio.sleep(config.POLL_INTERVAL)

"""Bot logic."""

import asyncio
import random
from asyncio import Task

from aiogram import Bot, Dispatcher, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, ErrorEvent, ForceReply, KeyboardButton, Message, ReplyKeyboardMarkup

from config import DEFAULT_PHRASES, Buttons, States, Urls, config
from logger import logger
from utils.db import db
from utils.middlewares import LogHandlers, ValidateChatType
from utils.polling import poll_practicum_updates
from utils.report import create_report
from utils.types import UserStatus

router = Router()
polling_task: Task[object] | None = None


def build_keyboard(user_status: UserStatus) -> ReplyKeyboardMarkup:
    """Build keyboard based on user state.

    Args:
        user_status: current user status.

    Returns:
        Keyboard layout for current user.
    """
    if not user_status["registered"]:
        first_button = KeyboardButton(text=Buttons.REGISTER_TEXT)
    elif user_status["enabled"]:
        first_button = KeyboardButton(text=Buttons.STOP_TEXT)
    else:
        first_button = KeyboardButton(text=Buttons.NOTIFY_TEXT)

    return ReplyKeyboardMarkup(
        keyboard=[[first_button], [KeyboardButton(text=Buttons.REPORT_TEXT)], [KeyboardButton(text=Buttons.HELP)]],
        resize_keyboard=True,
        input_field_placeholder="Choose an action",
    )


async def get_user_id(message: Message) -> int | None:
    """Get user from message.

    Args:
        message (Message): received message.

    Returns:
        int: user id.
    """
    user = message.from_user
    if user is None:
        await message.answer("This bot works only in private chats for security reasons.")
        return None
    return user.id


@router.message(CommandStart())
async def start(message: Message) -> None:
    """Handle start command.

    Args:
        message: received message.
    """
    if not (user_id := await get_user_id(message)):
        return
    status = await db.get_user_status(user_id)
    await message.answer("Welcome! What is thy bidding, my master?", reply_markup=build_keyboard(status))


@router.message(F.text == Buttons.REGISTER_TEXT)
async def register(message: Message, state: FSMContext) -> None:
    """Start registration flow: request token from user.

    Args:
        message: received message.
        state: bot state.
    """
    if not (user_id := await get_user_id(message)):
        return
    status = await db.get_user_status(user_id)
    if status.get("registered"):
        await message.answer("You are already registered.")
        return
    await state.set_state(States.waiting_for_token)
    await message.answer(
        "🔐 Please send me your Yandex.Practicum OAuth token in reply to this message.\n"
        "Your token will be securely stored and never shown again. Registration link:\n"
        f"{Urls.OAUTH_URL}",
        reply_markup=ForceReply(selective=True, input_field_placeholder="Paste your token here..."),
        protect_content=True,
    )


@router.message(States.waiting_for_token)
async def receive_token(message: Message, state: FSMContext) -> None:
    """Handle token sent by user, save via backend.

    Args:
        message: received message.
        state: bot state.
    """
    if not (user_id := await get_user_id(message)):
        return
    token = (message.text or "").strip()

    if not token:
        await message.reply("❌ Received empty token.")
        return
    if len(token.split()) > 1:
        await message.reply("❌ Too many tokens.")
        return
    try:
        await db.register_user(user_id, token=token)
    except Exception as ex:
        logger.exception("Internal registration error", exc_info=ex)
        await message.reply("❌ Registration failed. Internal error")
        await state.clear()
        return
    finally:
        await message.delete()
    await state.clear()
    status = await db.get_user_status(user_id)
    await message.answer(
        "✅ Registration successful! You can now subscribe to homework notifications.\n"
        "Use the menu buttons to manage them.",
        reply_markup=build_keyboard(status),
    )


@router.message(F.text == Buttons.NOTIFY_TEXT)
async def enable_notifications(message: Message) -> None:
    """Enable homework notifications.

    Args:
        message: received message.
    """
    if not (user_id := await get_user_id(message)):
        return
    await db.set_enabled(user_id, enabled=True)

    status = await db.get_user_status(user_id)
    await message.answer("Notifications are enabled.", reply_markup=build_keyboard(status))


@router.message(F.text == Buttons.STOP_TEXT)
async def disable_notifications(message: Message) -> None:
    """Disable homework notifications.

    Args:
        message: received message.
    """
    if not (user_id := await get_user_id(message)):
        return
    await db.set_enabled(user_id, enabled=False)
    status = await db.get_user_status(user_id)
    await message.answer("Notifications are disabled.", reply_markup=build_keyboard(status))


@router.message(F.text == Buttons.REPORT_TEXT)
async def full_report(message: Message) -> None:
    """Get full homeworks report.

    Args:
        message: received message.
    """
    wait_msg = await message.answer("⏳ Generating report, please wait...")
    if not (user_id := await get_user_id(message)):
        return
    status = await db.get_user_status(user_id)
    token = await db.get_user_token(user_id)
    if not token:
        await message.answer("You need to register first.", reply_markup=build_keyboard(status))
        return

    try:
        report_data = await create_report(token)
        await message.answer_document(
            document=BufferedInputFile(report_data.read(), filename="hw_report.xlsx"),
            caption="📊 Here is your full homework report.",
            reply_markup=build_keyboard(status),  # чтобы клавиатура осталась
        )
        logger.info(f"Report sent to user {user_id}")
    except Exception as ex:
        logger.exception(f"Failed to generate/send report for user {user_id}: {ex}")
        await message.answer(
            "❌ Failed to generate report. Please try again later.",
            reply_markup=build_keyboard(status),
        )
    finally:
        await wait_msg.delete()


@router.message(F.text == Buttons.HELP)
async def help_handler(message: Message) -> None:
    """Write helping information for user.

    Args:
        message: received message.
    """
    await start(message)


@router.errors()
async def handle_errors(event: ErrorEvent) -> bool:
    """Handle forbidden error during bot actions.

    Args:
        event: forbidden error.

    Returns:
        True if error handled successfully else False.
    """
    if not isinstance(event.exception, TelegramForbiddenError):
        return False
    logger.warning(f"Caught Forbidden error: {event.exception}")
    user_id: int | None = None
    if event.update.message:
        if not (user_id := await get_user_id(event.update.message)):
            return False
    elif event.update.callback_query:
        user_id = event.update.callback_query.from_user.id
    if not user_id:
        return False
    logger.info(f"User {user_id} blocked the bot. Disabling notifications.")
    await db.set_enabled(user_id, enabled=False)
    return True


@router.message()
async def default_handler(message: Message) -> None:
    """Fallback handler for unrecognized messages.

    Args:
        message: received message.
    """
    phrase = random.choice(DEFAULT_PHRASES)  # noqa: S311 - not cryptographic purposes
    await message.reply(phrase)


async def on_startup(bot: Bot) -> None:  # noqa: RUF029
    """Start polling at the bot startup.

    Args:
        bot: telegram bot handler.
    """
    global polling_task
    polling_task = asyncio.create_task(poll_practicum_updates(bot))
    logger.info("Polling task started")


async def on_shutdown() -> None:  # noqa: RUF029
    """Stop polling task on shutdown."""
    global polling_task
    if polling_task:
        polling_task.cancel()
        logger.info("Polling task cancelled")


async def main() -> None:
    """Entry point."""
    await db.create_users()

    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    dp = Dispatcher()
    dp.include_router(router)

    # middlewares
    dp.message.middleware(LogHandlers())
    dp.message.middleware(ValidateChatType())

    # Register the hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

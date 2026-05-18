"""Additional utils."""

from collections.abc import Awaitable, Callable, Mapping

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, TelegramObject

from logger import logger


class ValidateChatType(BaseMiddleware):
    """Validate chat type before any action."""

    async def __call__[RetVal, Event: TelegramObject, Data: Mapping[str, object]](
        self,
        handler: Callable[[Event, Data], Awaitable[RetVal]],
        event: Event,
        data: Data,
    ) -> RetVal | None:
        """Validate chat type and then use handler.

        Args:
            handler: Wrapped handler in middlewares chain
            event: Incoming event (Subclass of :class:`aiogram.types.base.TelegramObject`)
            data: Contextual data. Will be mapped to handler arguments

        Returns:
            Handler value.
        """
        if isinstance(event, Message):
            if event.chat.type != ChatType.PRIVATE:
                await event.answer("This bot works only in private chats for security reasons.")
                return None

        result = await handler(event, data)
        return result


class LogHandlers(BaseMiddleware):
    """Validate chat type before any action."""

    async def __call__[RetVal, Event: TelegramObject, Data: Mapping[str, object]](
        self,
        handler: Callable[[Event, Data], Awaitable[RetVal]],
        event: Event,
        data: Data,
    ) -> RetVal | None:
        """Validate chat type and then use handler.

        Args:
            handler: Wrapped handler in middlewares chain
            event: Incoming event (Subclass of :class:`aiogram.types.base.TelegramObject`)
            data: Contextual data. Will be mapped to handler arguments

        Returns:
            Handler value.
        """
        handler_name = getattr(handler, "__name__", str(handler))
        try:
            result = await handler(event, data)
            logger.debug('Call handler "%s" with arguments %s, %s returns %s', handler_name, event, data, result)
            return result
        except Exception as ex:
            logger.error('Call handler "%s" with arguments %s, %s raises %s', handler_name, event, data, ex)
            raise

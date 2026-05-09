"""Test bot actions."""

from aiogram.types import ReplyKeyboardMarkup

from bot import build_keyboard
from config import Buttons
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

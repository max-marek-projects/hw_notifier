"""Database handling."""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import aiosqlite

from config import config

from .types import ActiveUser, UserStatus


class DB:
    """Async SQLite database handler with Pydantic validation."""

    def __init__(self, db_path: Path) -> None:
        """Initialize database handler.

        Args:
            db_path: path to db file.
        """
        self.db_path = db_path

    async def create_users(self) -> None:
        """Create database table."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""--sql
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    practicum_token TEXT NOT NULL,
                    enabled INTEGER DEFAULT 0,
                    last_timestamp INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    @asynccontextmanager
    async def _connect(self) -> AsyncIterator[aiosqlite.Connection]:
        """Connect to database and require dictionary return values.

        Yields:
            Connection handler with dictionary as query return value.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def register_user(self, user_id: int, *, token: str) -> None:
        """Register or update user.

        Args:
            user_id: telegram user id.
            token: practicum access token.
        """
        async with self._connect() as db:
            int(datetime.now().timestamp())
            await db.execute(
                """--sql
                INSERT OR REPLACE INTO users (user_id, practicum_token, last_timestamp)
                    VALUES (?, ?, ?)
            """,
                parameters=(user_id, token, int(time.time())),
            )
            await db.commit()

    async def get_user_status(self, user_id: int) -> UserStatus:
        """Get user data.

        Args:
            user_id: id of telegram user.

        Returns:
            Response with user bool data.
        """
        async with self._connect() as db:
            async with db.execute(
                """--sql
                SELECT practicum_token, enabled FROM users
                    WHERE user_id = ?
                """,
                parameters=(user_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return {"registered": False, "enabled": False, "has_token": False}
        return {"registered": True, "enabled": bool(row["enabled"]), "has_token": bool(row["practicum_token"])}

    async def set_enabled(self, user_id: int, *, enabled: bool) -> None:
        """Включить или выключить уведомления для пользователя.

        Args:
            user_id: id of current telegram user.
            enabled: notifications are enabled (True/False).
        """
        async with self._connect() as db:
            await db.execute(
                """--sql
                UPDATE users SET enabled = ?
                    WHERE user_id = ?
                """,
                (1 if enabled else 0, user_id),
            )
            await db.commit()

    async def update_last_timestamp(self, user_id: int, *, timestamp: int) -> None:
        """Update last timestamp.

        Args:
            user_id: id of current telegram user.
            timestamp: last homework update timestamp.
        """
        async with self._connect() as db:
            await db.execute(
                """--sql
                UPDATE users SET last_timestamp = MAX(last_timestamp, ?) 
                    WHERE user_id = ?
                """,
                parameters=(timestamp, user_id),
            )
            await db.commit()

    async def get_active_users(self) -> list[ActiveUser]:
        """Get all active users.

        Returns:
            list of all active users data.
        """
        async with self._connect() as db:
            async with db.execute("""--sql
                SELECT user_id, practicum_token, last_timestamp FROM users
                    WHERE enabled = 1 AND practicum_token IS NOT NULL
            """) as cursor:
                rows = await cursor.fetchall()
        return [
            {
                "user_id": row["user_id"],
                "practicum_token": row["practicum_token"],
                "last_timestamp": row["last_timestamp"],
            }
            for row in rows
        ]

    async def get_user_token(self, user_id: int) -> str | None:
        """Get current user practicum token if it exists.

        Args:
            user_id: id of current user.

        Returns:
            Practicum token from db or None.
        """
        async with self._connect() as db:
            async with db.execute("SELECT practicum_token FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
        return row["practicum_token"] if row else None


db = DB(config.DB_PATH)

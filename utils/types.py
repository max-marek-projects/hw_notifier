"""All custom types for bot."""

from typing import TypedDict

# homework response


class HWItem(TypedDict):
    """Single homework item in response."""

    id: int
    status: str
    homework_name: str
    reviewer_comment: str
    date_updated: str
    lesson_name: str


class HWResponse(TypedDict):
    """Homework response.

    Attributes:
        homeworks: list of homework updates data.
        current_date: current timestamp.
    """

    homeworks: list[HWItem]
    current_date: int


# database response values


class UserStatus(TypedDict):
    """Current user status from database.

    Attributes:
        registered: is this user registered.
        enabled: are notifications enabled for this user.
        has_token: does this user has token in db.
    """

    registered: bool
    enabled: bool
    has_token: bool


class ActiveUser(TypedDict):
    """Active user data.

    Attributes:
        user_id: id of telegram user.
        practicum_token: token to access practicum endpoint.
        last_timestamp: last homework update time.
    """

    user_id: int
    practicum_token: str
    last_timestamp: int

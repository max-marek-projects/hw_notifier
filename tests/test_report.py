"""Test report generation."""

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from utils.report import create_report


@pytest.mark.asyncio
async def test_create_report() -> None:
    """Test report creation."""
    mock_homeworks = [
        {
            "id": 1,
            "status": "approved",
            "homework_name": "HW1",
            "reviewer_comment": "ok",
            "date_updated": "2025-01-01T00:00:00Z",
            "lesson_name": "Lesson1",
        },
        {
            "id": 2,
            "status": "reviewing",
            "homework_name": "HW2",
            "reviewer_comment": "",
            "date_updated": "2025-01-02T00:00:00Z",
            "lesson_name": "Lesson2",
        },
    ]
    with patch("utils.report.get_api_answer", new=AsyncMock(return_value=mock_homeworks)):
        content = await create_report("fake_token")
    assert content.readable()
    content.seek(0)
    df = pd.read_excel(content, sheet_name="Homeworks")
    assert len(df) == 2
    assert list(df.columns) == ["id", "status", "homework_name", "reviewer_comment", "date_updated", "lesson_name"]
    assert df.iloc[0]["id"] == 1

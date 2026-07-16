from datetime import datetime, timedelta, timezone

import pytest

from app.services.relationship_service import RelationshipService


@pytest.mark.parametrize(
    ("days_ago", "expected"),
    [(7, 100), (8, 80), (14, 80), (15, 50), (30, 50), (31, 20), (60, 20), (61, 0)],
)
def test_freshness_decay_boundaries(days_ago: int, expected: int):
    now = datetime(2026, 7, 14, 12, tzinfo=timezone.utc)
    assert RelationshipService.freshness_for(now - timedelta(days=days_ago), now) == expected


def test_freshness_normalizes_timezone_and_future_timestamps():
    now = datetime(2026, 7, 14, 12, tzinfo=timezone.utc)
    offset_time = datetime(2026, 7, 7, 17, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    assert RelationshipService.freshness_for(offset_time, now) == 100
    assert RelationshipService.freshness_for(now + timedelta(hours=1), now) == 100


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "cold"),
        (29, "cold"),
        (30, "needs_attention"),
        (59, "needs_attention"),
        (60, "healthy"),
        (79, "healthy"),
        (80, "strong"),
    ],
)
def test_relationship_health_boundaries(score: int, expected: str):
    assert RelationshipService.health_for(score) == expected

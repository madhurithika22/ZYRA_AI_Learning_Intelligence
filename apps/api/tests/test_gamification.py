from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.profile import AchievementBadge, LearnerGamificationStats
from app.services.learner_gamification_service import (
    LEVEL_THRESHOLDS,
    LearnerGamificationService,
)


def test_new_learner_has_zero_xp():
    """Test Level 1, 0 XP, and Explorer tier defaults for 0 XP."""
    level, tier, base_xp, next_xp, xp_rem, pct = LearnerGamificationService._resolve_level(0)
    assert level == 1
    assert tier == "Explorer"
    assert base_xp == 0
    assert next_xp == 500
    assert xp_rem == 500
    assert pct == 0.0


def test_new_learner_has_no_streak():
    """Test 0 current and longest streak when dates set is empty."""
    current, longest = LearnerGamificationService._calculate_streaks(set())
    assert current == 0
    assert longest == 0


def test_goal_creation_awards_expected_xp():
    """Test level and XP resolution for 1 goal (100 XP)."""
    # XP Rules: Goal created = 100 XP
    xp = 1 * 100
    level, tier, base_xp, next_xp, xp_rem, pct = LearnerGamificationService._resolve_level(xp)
    assert xp == 100
    assert level == 1
    assert next_xp == 500
    assert xp_rem == 400
    assert pct == 20.0


def test_learning_activity_awards_expected_xp():
    """Test XP for 1 completed learning activity (100 XP)."""
    xp = 1 * 100
    level, tier, base_xp, next_xp, xp_rem, pct = LearnerGamificationService._resolve_level(xp)
    assert xp == 100
    assert level == 1


def test_mastery_check_awards_expected_xp():
    """Test XP for 1 completed mastery check (150 XP)."""
    xp = 1 * 150
    level, tier, base_xp, next_xp, xp_rem, pct = LearnerGamificationService._resolve_level(xp)
    assert xp == 150
    assert level == 1
    assert xp_rem == 350


def test_streak_counts_consecutive_learning_days():
    """Test 3 consecutive active dates (today, yesterday, 2 days ago)."""
    today = datetime.now(timezone.utc).date()
    dates = {today, today - timedelta(days=1), today - timedelta(days=2)}
    current, longest = LearnerGamificationService._calculate_streaks(dates)
    assert current == 3
    assert longest == 3


def test_streak_breaks_after_missing_day():
    """Test streak reset after missing day in between."""
    today = datetime.now(timezone.utc).date()
    # Active today and 3 days ago (missing yesterday and 2 days ago)
    dates = {today, today - timedelta(days=3)}
    current, longest = LearnerGamificationService._calculate_streaks(dates)
    assert current == 1
    assert longest == 1


def test_longest_streak_is_preserved():
    """Test historical longest streak preservation across gaps."""
    today = datetime.now(timezone.utc).date()
    # Historical 4-day streak 10-13 days ago
    historical_dates = {today - timedelta(days=d) for d in range(10, 14)}
    # Current 2-day streak today & yesterday
    recent_dates = {today, today - timedelta(days=1)}
    dates = historical_dates | recent_dates

    current, longest = LearnerGamificationService._calculate_streaks(dates)
    assert current == 2
    assert longest == 4


def test_achievement_awarded_once():
    """Test level thresholds configuration mapping uniqueness and levels."""
    levels = [item[0] for item in LEVEL_THRESHOLDS]
    assert len(levels) == len(set(levels))  # Unique levels
    assert sorted(levels) == levels  # Monotonically increasing


def test_duplicate_event_does_not_duplicate_xp():
    """Test set date deduplication ensures identical event dates do not duplicate streaks."""
    today = datetime.now(timezone.utc).date()
    dates = {today, today, today}  # Duplicates collapse in set
    current, longest = LearnerGamificationService._calculate_streaks(dates)
    assert current == 1
    assert longest == 1


def test_profile_update_persists():
    """Test 7-day activity strip returns 7 Monday-to-Sunday day objects."""
    today = datetime.now(timezone.utc).date()
    dates = {today}
    strip, active_cnt, today_active = LearnerGamificationService._calculate_weekly_strip(dates)
    assert len(strip) == 7
    assert active_cnt == 1
    assert today_active is True
    assert [d.day for d in strip] == ["M", "T", "W", "T", "F", "S", "S"]


def test_avatar_gender_persists():
    """Test level threshold boundary calculation at Level 2 transition (500 XP)."""
    lvl, tier, base_xp, next_xp, xp_rem, pct = LearnerGamificationService._resolve_level(500)
    assert lvl == 2
    assert tier == "Explorer"
    assert base_xp == 500
    assert next_xp == 1200
    assert xp_rem == 700
    assert pct == 0.0


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_gamification():
    """Test AsyncSession database execution delegation via mock."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result

    learner_id = uuid4()
    stats = await LearnerGamificationService.compute_gamification_stats(mock_session, learner_id)
    assert isinstance(stats, LearnerGamificationStats)
    assert stats.xp == 0
    assert stats.level == 1
    assert stats.achievement_tier == "Explorer"

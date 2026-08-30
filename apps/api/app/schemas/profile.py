from typing import Any
from pydantic import BaseModel, Field


class LearnerProfileDetail(BaseModel):
    experience_level: str | None = None
    preferred_learning_mode: str | None = None
    weekly_availability_hours: float | None = None
    stated_background: str | None = None
    gender: str | None = None
    avatar_gender: str | None = None
    avatar_variant: str | None = None
    profile_metadata: dict[str, Any] | None = None


class AchievementBadge(BaseModel):
    id: str
    title: str
    description: str
    condition: str
    unlocked: bool
    unlocked_at: str | None = None
    earned_at: str | None = None
    icon: str


class WeeklyActivityDay(BaseModel):
    day: str
    date: str
    active: bool
    is_today: bool


class LearningIdentitySummary(BaseModel):
    target_role: str | None = None
    strongest_skill: str | None = None
    biggest_opportunity: str | None = None
    consistency_text: str = "No learning activity recorded this week"
    evidence_text: str = "0 verified outcomes"


class LearnerGamificationStats(BaseModel):
    streak_days: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    xp: int = 0
    level: int = 1
    achievement_tier: str = "Explorer"
    current_level_base_xp: int = 0
    next_level_xp: int = 500
    xp_remaining: int = 500
    level_progress_pct: float = 0.0
    evidence_count: int = 0
    weekly_activity_strip: list[WeeklyActivityDay] = Field(default_factory=list)
    weekly_active_days_count: int = 0
    today_active: bool = False
    strengths: list[str] = Field(default_factory=list)
    growth_areas: list[str] = Field(default_factory=list)
    identity_summary: LearningIdentitySummary = Field(default_factory=LearningIdentitySummary)
    achievements: list[AchievementBadge] = Field(default_factory=list)


class LearnerGoalProgressSummary(BaseModel):
    goal_id: str | None = None
    target_role: str | None = None
    progress_percentage: float = 0.0


class LearnerProfileResponse(BaseModel):
    learner_id: str
    display_name: str
    email: str
    profile: LearnerProfileDetail
    gamification: LearnerGamificationStats
    current_journey: LearnerGoalProgressSummary | None = None
    goals_count: int = 0


class LearnerProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    experience_level: str | None = None
    preferred_learning_mode: str | None = None
    weekly_availability_hours: float | None = None
    stated_background: str | None = None
    gender: str | None = None
    avatar_gender: str | None = None
    avatar_variant: str | None = None
    profile_metadata: dict[str, Any] | None = None

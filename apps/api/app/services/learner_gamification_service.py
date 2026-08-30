from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnostic_response import DiagnosticResponse
from app.models.goal import Goal
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path import LearningPath
from app.models.mastery_check_attempt import MasteryCheckAttempt
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.schemas.profile import (
    AchievementBadge,
    LearnerGamificationStats,
    LearningIdentitySummary,
    WeeklyActivityDay,
)

# Central level threshold & achievement tier configuration
LEVEL_THRESHOLDS: list[tuple[int, int, str]] = [
    (1, 0, "Explorer"),
    (2, 500, "Explorer"),
    (3, 1200, "Builder"),
    (4, 2000, "Builder"),
    (5, 3000, "Practitioner"),
    (6, 4500, "Practitioner"),
    (7, 6500, "Proficient"),
    (8, 9000, "Proficient"),
    (9, 12000, "Mastery Seeker"),
    (10, 16000, "Mastery Seeker"),
]


class LearnerGamificationService:
    """Event-driven service calculating honest streaks, deterministic XP, 7-day activity strip, strengths/growth areas, and identity summary."""

    @staticmethod
    async def compute_gamification_stats(
        session: AsyncSession, learner_id: UUID
    ) -> LearnerGamificationStats:
        # 1. Gather meaningful learning event dates & calculate streaks
        dates = await LearnerGamificationService._get_meaningful_dates(session, learner_id)
        current_streak, longest_streak = LearnerGamificationService._calculate_streaks(dates)

        # 2. Compute 7-day activity strip for current UTC week (Monday to Sunday)
        strip, weekly_active_cnt, today_active = LearnerGamificationService._calculate_weekly_strip(dates)

        # 3. Query event counts & calculate deterministic XP
        (
            goals_cnt,
            diag_cnt,
            act_completed_cnt,
            mastery_cnt,
            evidence_cnt,
            paths_cnt,
        ) = await LearnerGamificationService._get_event_counts(session, learner_id)

        # XP Rules:
        # Goal created = 100 XP
        # Diagnostic response = 150 XP
        # Learning activity completed = 100 XP
        # Mastery check completed = 150 XP
        # Skill evidence verified = 250 XP
        # Learning path accepted = 50 XP
        xp = (
            (goals_cnt * 100)
            + (diag_cnt * 150)
            + (act_completed_cnt * 100)
            + (mastery_cnt * 150)
            + (evidence_cnt * 250)
            + (paths_cnt * 50)
        )

        # 4. Resolve level & achievement tier
        (
            level,
            tier,
            base_xp,
            next_xp,
            xp_rem,
            progress_pct,
        ) = LearnerGamificationService._resolve_level(xp)

        # 5. Evaluate 7 explicit achievements with genuine condition checking & earned_at timestamps
        achievements = await LearnerGamificationService._evaluate_achievements(
            session, learner_id, current_streak, longest_streak
        )

        # 6. Derive genuine Strengths & Growth Areas from SkillMastery
        strengths, growth_areas = await LearnerGamificationService._get_strengths_and_growth_areas(
            session, learner_id
        )

        # 7. Generate Personal Learning Identity Summary
        identity_summary = await LearnerGamificationService._get_identity_summary(
            session, learner_id, strengths, growth_areas, weekly_active_cnt, evidence_cnt
        )

        return LearnerGamificationStats(
            streak_days=current_streak,
            current_streak=current_streak,
            longest_streak=longest_streak,
            xp=xp,
            level=level,
            achievement_tier=tier,
            current_level_base_xp=base_xp,
            next_level_xp=next_xp,
            xp_remaining=xp_rem,
            level_progress_pct=progress_pct,
            evidence_count=evidence_cnt,
            weekly_activity_strip=strip,
            weekly_active_days_count=weekly_active_cnt,
            today_active=today_active,
            strengths=strengths,
            growth_areas=growth_areas,
            identity_summary=identity_summary,
            achievements=achievements,
        )

    @staticmethod
    def _calculate_weekly_strip(dates: set[datetime.date]) -> tuple[list[WeeklyActivityDay], int, bool]:
        """Generate Monday-to-Sunday activity strip for current UTC week."""
        today = datetime.now(timezone.utc).date()
        start_of_week = today - timedelta(days=today.weekday())  # Monday

        days_names = ["M", "T", "W", "T", "F", "S", "S"]
        strip: list[WeeklyActivityDay] = []
        active_cnt = 0
        today_active = False

        for i in range(7):
            d = start_of_week + timedelta(days=i)
            is_active = d in dates
            is_today = (d == today)
            if is_active:
                active_cnt += 1
            if is_today and is_active:
                today_active = True

            strip.append(
                WeeklyActivityDay(
                    day=days_names[i],
                    date=d.isoformat(),
                    active=is_active,
                    is_today=is_today,
                )
            )

        return strip, active_cnt, today_active

    @staticmethod
    async def _get_strengths_and_growth_areas(
        session: AsyncSession, learner_id: UUID
    ) -> tuple[list[str], list[str]]:
        """Derive strengths (mastery >= 0.7) and growth areas (mastery < 0.7) from SkillMastery."""
        stmt = (
            select(Skill.name, SkillMastery.mastery_score)
            .join(Skill, SkillMastery.skill_id == Skill.id)
            .where(SkillMastery.learner_id == learner_id)
            .order_by(SkillMastery.mastery_score.desc())
        )
        res = await session.execute(stmt)
        rows = res.all()

        strengths: list[str] = []
        growth_areas: list[str] = []

        for name, score in rows:
            if score >= 0.7:
                strengths.append(name)
            else:
                growth_areas.append(name)

        return strengths, growth_areas

    @staticmethod
    async def _get_identity_summary(
        session: AsyncSession,
        learner_id: UUID,
        strengths: list[str],
        growth_areas: list[str],
        weekly_active_cnt: int,
        evidence_cnt: int,
    ) -> LearningIdentitySummary:
        """Construct Personal Learning Identity summary derived from real backend data."""
        # Query target role name from active goal
        g_stmt = (
            select(Role.name)
            .select_from(Goal)
            .join(Role, Goal.target_role_id == Role.id)
            .where(Goal.learner_id == learner_id)
            .order_by(Goal.created_at.desc())
            .limit(1)
        )
        role_res = (await session.execute(g_stmt)).scalar()
        if not role_res:
            # Fallback to direct Goal.target_role_id if join returned none
            fallback_stmt = (
                select(Goal.target_role_id)
                .where(Goal.learner_id == learner_id)
                .order_by(Goal.created_at.desc())
                .limit(1)
            )
            fallback_res = (await session.execute(fallback_stmt)).scalar()
            target_role = str(fallback_res) if fallback_res else None
        else:
            target_role = str(role_res)

        strongest_skill = strengths[0] if strengths else None
        biggest_opp = growth_areas[0] if growth_areas else None

        consistency_text = f"{weekly_active_cnt} active days this week" if weekly_active_cnt > 0 else "0 active days this week"
        evidence_text = f"{evidence_cnt} verified outcomes"

        return LearningIdentitySummary(
            target_role=target_role,
            strongest_skill=strongest_skill,
            biggest_opportunity=biggest_opp,
            consistency_text=consistency_text,
            evidence_text=evidence_text,
        )

    @staticmethod
    async def _evaluate_achievements(
        session: AsyncSession,
        learner_id: UUID,
        current_streak: int,
        longest_streak: int,
    ) -> list[AchievementBadge]:
        """Evaluate the 7 explicit achievements with real event timestamps."""
        achievements: list[AchievementBadge] = []

        # 1. FIRST STEP: Defined your first learning goal
        g_stmt = select(func.min(Goal.created_at)).where(Goal.learner_id == learner_id)
        t_g = (await session.execute(g_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="first_step",
                title="FIRST STEP",
                description="Defined your first learning goal.",
                condition="Create at least 1 career goal",
                unlocked=t_g is not None,
                unlocked_at=t_g.isoformat() if t_g else None,
                earned_at=t_g.isoformat() if t_g else None,
                icon="target",
            )
        )

        # 2. DIAGNOSTIC COMPLETE: Completed your first adaptive assessment
        d_stmt = select(func.min(DiagnosticResponse.created_at)).join(
            DiagnosticResponse.session
        ).where(DiagnosticResponse.session.has(learner_id=learner_id))
        t_d = (await session.execute(d_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="diagnostic_complete",
                title="DIAGNOSTIC COMPLETE",
                description="Completed your first adaptive assessment.",
                condition="Complete diagnostic knowledge mapping",
                unlocked=t_d is not None,
                unlocked_at=t_d.isoformat() if t_d else None,
                earned_at=t_d.isoformat() if t_d else None,
                icon="clipboard",
            )
        )

        # 3. FIRST PROOF: Submitted your first mastery evidence
        m_stmt = select(func.min(MasteryCheckAttempt.started_at)).where(
            MasteryCheckAttempt.learner_id == learner_id
        )
        t_m = (await session.execute(m_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="first_proof",
                title="FIRST PROOF",
                description="Submitted your first mastery evidence.",
                condition="Submit a mastery check assessment",
                unlocked=t_m is not None,
                unlocked_at=t_m.isoformat() if t_m else None,
                earned_at=t_m.isoformat() if t_m else None,
                icon="award",
            )
        )

        # 4. SKILL DEMONSTRATED: Proved mastery in a target skill
        sk_stmt = select(func.min(SkillMastery.updated_at)).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.mastery_score >= 0.8,
        )
        t_sk = (await session.execute(sk_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="skill_demonstrated",
                title="SKILL DEMONSTRATED",
                description="Proved mastery in a target skill.",
                condition="Achieve >= 80% mastery score in a skill",
                unlocked=t_sk is not None,
                unlocked_at=t_sk.isoformat() if t_sk else None,
                earned_at=t_sk.isoformat() if t_sk else None,
                icon="zap",
            )
        )

        # 5. CONSISTENT LEARNER: Maintained a 7-day learning streak
        is_consistent = current_streak >= 7 or longest_streak >= 7
        t_con = None
        if is_consistent:
            act_max_stmt = select(func.max(LearningActivityAttempt.completed_at)).where(
                LearningActivityAttempt.learner_id == learner_id
            )
            t_con = (await session.execute(act_max_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="consistent_learner",
                title="CONSISTENT LEARNER",
                description="Maintained a 7-day learning streak.",
                condition="Maintain a streak of 7 consecutive active days",
                unlocked=is_consistent,
                unlocked_at=t_con.isoformat() if t_con else None,
                earned_at=t_con.isoformat() if t_con else None,
                icon="flame",
            )
        )

        # 6. PATH ADAPTER: Accepted your first dynamically replanned path
        p_stmt = select(func.min(LearningPath.created_at)).where(
            LearningPath.learner_id == learner_id,
            (LearningPath.version > 1) | (LearningPath.parent_path_id.isnot(None)),
        )
        t_p = (await session.execute(p_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="path_adapter",
                title="PATH ADAPTER",
                description="Accepted your first dynamically replanned path.",
                condition="Accept a dynamically adapted learning path",
                unlocked=t_p is not None,
                unlocked_at=t_p.isoformat() if t_p else None,
                earned_at=t_p.isoformat() if t_p else None,
                icon="git-branch",
            )
        )

        # 7. EVIDENCE BUILDER: Recorded 5 verified learning outcomes
        e5_stmt = (
            select(SkillEvidence.created_at)
            .where(SkillEvidence.learner_id == learner_id)
            .order_by(SkillEvidence.created_at.asc())
            .offset(4)
            .limit(1)
        )
        t_e5 = (await session.execute(e5_stmt)).scalar()
        achievements.append(
            AchievementBadge(
                id="evidence_builder",
                title="EVIDENCE BUILDER",
                description="Recorded 5 verified learning outcomes.",
                condition="Accumulate 5 verified skill evidence entries",
                unlocked=t_e5 is not None,
                unlocked_at=t_e5.isoformat() if t_e5 else None,
                earned_at=t_e5.isoformat() if t_e5 else None,
                icon="shield",
            )
        )

        return achievements

    @staticmethod
    async def _get_meaningful_dates(session: AsyncSession, learner_id: UUID) -> set[datetime.date]:
        """Extract unique UTC calendar dates containing meaningful learning events."""
        dates: set[datetime.date] = set()

        # 1. Activity completions (status == 'completed')
        act_stmt = select(func.date(LearningActivityAttempt.completed_at)).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.status == "completed",
        )
        for d in (await session.execute(act_stmt)).scalars():
            if d:
                dates.add(d)

        # 2. Mastery check attempts
        m_stmt = select(func.date(MasteryCheckAttempt.started_at)).where(
            MasteryCheckAttempt.learner_id == learner_id
        )
        for d in (await session.execute(m_stmt)).scalars():
            if d:
                dates.add(d)

        # 3. Diagnostic responses
        d_stmt = select(func.date(DiagnosticResponse.created_at)).join(
            DiagnosticResponse.session
        ).where(DiagnosticResponse.session.has(learner_id=learner_id))
        for d in (await session.execute(d_stmt)).scalars():
            if d:
                dates.add(d)

        # 4. Skill evidence
        e_stmt = select(func.date(SkillEvidence.created_at)).where(
            SkillEvidence.learner_id == learner_id
        )
        for d in (await session.execute(e_stmt)).scalars():
            if d:
                dates.add(d)

        return dates

    @staticmethod
    def _calculate_streaks(dates: set[datetime.date]) -> tuple[int, int]:
        """Compute current and longest streak from unique UTC activity dates."""
        if not dates:
            return 0, 0

        sorted_dates = sorted(dates)

        # 1. Longest streak
        longest_streak = 1
        current_run = 1

        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                current_run += 1
                if current_run > longest_streak:
                    longest_streak = current_run
            elif sorted_dates[i] > sorted_dates[i - 1] + timedelta(days=1):
                current_run = 1

        # 2. Current streak
        today = datetime.now(timezone.utc).date()
        current_streak = 0
        check_date = today

        # If no activity today, check if yesterday had activity
        if check_date not in dates:
            check_date = today - timedelta(days=1)

        while check_date in dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        return current_streak, longest_streak

    @staticmethod
    async def _get_event_counts(session: AsyncSession, learner_id: UUID) -> tuple[int, int, int, int, int, int]:
        """Query count of goals, diagnostics, activity completions, mastery checks, evidence, and paths."""
        goals_stmt = select(func.count(Goal.id)).where(Goal.learner_id == learner_id)
        goals_cnt = (await session.execute(goals_stmt)).scalar() or 0

        diag_stmt = select(func.count(DiagnosticResponse.id)).join(
            DiagnosticResponse.session
        ).where(DiagnosticResponse.session.has(learner_id=learner_id))
        diag_cnt = (await session.execute(diag_stmt)).scalar() or 0

        act_stmt = select(func.count(LearningActivityAttempt.id)).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.status == "completed",
        )
        act_completed_cnt = (await session.execute(act_stmt)).scalar() or 0

        m_stmt = select(func.count(MasteryCheckAttempt.id)).where(
            MasteryCheckAttempt.learner_id == learner_id
        )
        mastery_cnt = (await session.execute(m_stmt)).scalar() or 0

        ev_stmt = select(func.count(SkillEvidence.id)).where(
            SkillEvidence.learner_id == learner_id
        )
        evidence_cnt = (await session.execute(ev_stmt)).scalar() or 0

        p_stmt = select(func.count(LearningPath.id)).where(
            LearningPath.learner_id == learner_id
        )
        paths_cnt = (await session.execute(p_stmt)).scalar() or 0

        return goals_cnt, diag_cnt, act_completed_cnt, mastery_cnt, evidence_cnt, paths_cnt

    @staticmethod
    def _resolve_level(xp: int) -> tuple[int, str, int, int, int, float]:
        """Resolve current level, tier, base threshold, next threshold, xp remaining, and percentage."""
        current_lvl = 1
        current_tier = "Explorer"
        base_xp = 0
        next_xp = 500

        for i, (lvl, req_xp, tier) in enumerate(LEVEL_THRESHOLDS):
            if xp >= req_xp:
                current_lvl = lvl
                current_tier = tier
                base_xp = req_xp
                if i + 1 < len(LEVEL_THRESHOLDS):
                    next_xp = LEVEL_THRESHOLDS[i + 1][1]
                else:
                    # Max level ceiling
                    next_xp = req_xp + 5000

        xp_in_level = xp - base_xp
        level_span = next_xp - base_xp
        xp_remaining = max(0, next_xp - xp)
        progress_pct = round(min(100.0, max(0.0, (xp_in_level / level_span) * 100)), 1)

        return current_lvl, current_tier, base_xp, next_xp, xp_remaining, progress_pct

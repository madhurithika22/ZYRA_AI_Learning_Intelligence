from uuid import UUID

from app.models.diagnostic_session import DiagnosticSession
from app.models.goal import Goal
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path import LearningPath
from app.models.mastery_check_attempt import MasteryCheckAttempt
from app.schemas.app_state import LearnerAppStateResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class AppStateService:
    @staticmethod
    async def get_learner_app_state(
        db: AsyncSession, learner_id: UUID
    ) -> LearnerAppStateResponse:
        # 1. Fetch latest Goal with target_role eagerly loaded
        stmt = (
            select(Goal)
            .where(Goal.learner_id == learner_id)
            .options(selectinload(Goal.target_role))
            .order_by(Goal.created_at.desc())
        )
        res = await db.execute(stmt)
        goal = res.scalars().first()

        role_title = None
        if goal:
            if hasattr(goal, "target_role") and goal.target_role:
                role_title = getattr(goal.target_role, "name", None) or getattr(goal.target_role, "title", None) or goal.objective
            else:
                role_title = goal.objective

        if not goal:
            return LearnerAppStateResponse(
                learner_id=learner_id,
                stage="GOAL_REQUIRED",
                next_action_label="Define My Goal",
                next_action_route="goal",
            )

        # 2. Fetch latest Diagnostic Session
        stmt_diag = (
            select(DiagnosticSession)
            .where(DiagnosticSession.goal_id == goal.id)
            .order_by(DiagnosticSession.created_at.desc())
        )
        res_diag = await db.execute(stmt_diag)
        diag = res_diag.scalars().first()

        if not diag:
            return LearnerAppStateResponse(
                learner_id=learner_id,
                stage="DIAGNOSTIC_REQUIRED",
                next_action_label="Start Diagnostic",
                next_action_route="diagnostic",
                goal_id=goal.id,
                target_role=role_title,
            )

        if diag.status == "in_progress":
            return LearnerAppStateResponse(
                learner_id=learner_id,
                stage="DIAGNOSTIC_IN_PROGRESS",
                next_action_label="Continue Diagnostic",
                next_action_route="diagnostic",
                goal_id=goal.id,
                target_role=role_title,
                diagnostic_session_id=diag.id,
            )

        # 3. Fetch latest Learning Path
        stmt_path = (
            select(LearningPath)
            .where(LearningPath.goal_id == goal.id)
            .order_by(LearningPath.created_at.desc())
        )
        res_path = await db.execute(stmt_path)
        path = res_path.scalars().first()

        if not path:
            return LearnerAppStateResponse(
                learner_id=learner_id,
                stage="PATH_SELECTION",
                next_action_label="Generate My Learning Path",
                next_action_route="path",
                goal_id=goal.id,
                target_role=role_title,
                diagnostic_session_id=diag.id,
            )

        # 4. Check for Learning Activity and Mastery Check Attempts
        stmt_act = (
            select(LearningActivityAttempt)
            .where(LearningActivityAttempt.learner_id == learner_id)
            .order_by(LearningActivityAttempt.started_at.desc())
        )
        res_act = await db.execute(stmt_act)
        act = res_act.scalars().first()

        stmt_mc = (
            select(MasteryCheckAttempt)
            .where(MasteryCheckAttempt.learner_id == learner_id)
            .order_by(MasteryCheckAttempt.started_at.desc())
        )
        res_mc = await db.execute(stmt_mc)
        mc = res_mc.scalars().first()

        if act and not mc:
            return LearnerAppStateResponse(
                learner_id=learner_id,
                stage="PROOF_REQUIRED",
                next_action_label="Prove My Mastery",
                next_action_route="proof",
                goal_id=goal.id,
                target_role=role_title,
                active_path_id=path.id,
                diagnostic_session_id=diag.id,
            )

        if mc:
            return LearnerAppStateResponse(
                learner_id=learner_id,
                stage="ADAPTIVE_CONTINUATION",
                next_action_label="View Learning Twin",
                next_action_route="overview",
                goal_id=goal.id,
                target_role=role_title,
                active_path_id=path.id,
                diagnostic_session_id=diag.id,
            )

        return LearnerAppStateResponse(
            learner_id=learner_id,
            stage="ACTIVE_LEARNING",
            next_action_label="Continue Learning Activity",
            next_action_route="activity",
            goal_id=goal.id,
            target_role=role_title,
            active_path_id=path.id,
            diagnostic_session_id=diag.id,
        )

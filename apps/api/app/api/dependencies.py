from typing import Any
from uuid import UUID

from app.core.database import get_db_session
from app.core.security import decode_session_token
from app.models.learner import Learner
from app.models.user_account import UserAccount
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_session_payload(request: Request) -> dict[str, Any]:
    """Extract and validate Fernet session payload from HttpOnly cookie or Authorization Bearer header."""
    cookie_token = request.cookies.get("session_id")
    auth_header = request.headers.get("Authorization")

    token: str | None = cookie_token
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
        )

    payload = decode_session_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or expired. Please sign in again.",
        )

    return payload


async def get_current_user_account(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> UserAccount:
    """Resolve authenticated UserAccount from session token."""
    payload = await get_current_session_payload(request)
    user_id_str = payload.get("user_id")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token payload.",
        )

    try:
        user_uuid = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in session.",
        )

    stmt = select(UserAccount).where(UserAccount.id == user_uuid)
    res = await session.execute(stmt)
    user_account = res.scalar_one_or_none()

    if not user_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    return user_account


async def get_current_learner(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> Learner:
    """Resolve authenticated Learner from session token. Ensures 1:1 user ↔ learner identity."""
    user_account = await get_current_user_account(request, session)

    stmt = select(Learner).where(Learner.id == user_account.learner_id)
    res = await session.execute(stmt)
    learner = res.scalar_one_or_none()

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Associated learner record not found.",
        )

    return learner


def verify_learner_access(target_learner_id: UUID, current_learner: Learner) -> None:
    """Verify that current authenticated learner matches target learner ID (multi-tenant isolation)."""
    if target_learner_id != current_learner.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

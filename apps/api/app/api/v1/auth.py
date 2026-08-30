
from app.api.dependencies import get_current_user_account
from app.core.database import get_db_session
from app.core.security import (
    create_session_token,
    hash_password,
    verify_password,
)
from app.models.learner import Learner
from app.models.user_account import UserAccount
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    display_name: str = Field(..., min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUserResponse(BaseModel):
    user_id: str
    learner_id: str
    email: str
    display_name: str


@router.post(
    "/register",
    response_model=AuthUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account & learner",
)
async def register_user(
    payload: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> AuthUserResponse:
    """Create a new UserAccount + Learner, authenticate session, and set HttpOnly cookie."""
    clean_email = payload.email.lower().strip()

    # Check duplicate email
    existing_stmt = select(UserAccount).where(UserAccount.email == clean_email)
    existing_res = await session.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # 1. Create Learner
    learner = Learner(
        display_name=payload.display_name.strip(),
        email=clean_email,
    )
    session.add(learner)
    await session.flush()

    # 2. Create UserAccount
    pw_hash = hash_password(payload.password)
    user_account = UserAccount(
        learner_id=learner.id,
        email=clean_email,
        password_hash=pw_hash,
        display_name=payload.display_name.strip(),
    )
    session.add(user_account)
    await session.commit()
    await session.refresh(user_account)

    # 3. Create Session Token & Cookie
    session_token = create_session_token(
        user_id=str(user_account.id),
        learner_id=str(learner.id),
        email=clean_email,
    )

    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Local HTTP development compatibility
        path="/",
        max_age=7 * 24 * 3600,
    )

    return AuthUserResponse(
        user_id=str(user_account.id),
        learner_id=str(learner.id),
        email=clean_email,
        display_name=user_account.display_name,
    )


@router.post(
    "/login",
    response_model=AuthUserResponse,
    summary="Authenticate credentials and create session cookie",
)
async def login_user(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> AuthUserResponse:
    """Validate email & password. On success, set HttpOnly session cookie."""
    clean_email = payload.email.lower().strip()

    stmt = select(UserAccount).where(UserAccount.email == clean_email)
    res = await session.execute(stmt)
    user_account = res.scalar_one_or_none()

    if not user_account or not verify_password(payload.password, user_account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )

    session_token = create_session_token(
        user_id=str(user_account.id),
        learner_id=str(user_account.learner_id),
        email=clean_email,
    )

    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=7 * 24 * 3600,
    )

    return AuthUserResponse(
        user_id=str(user_account.id),
        learner_id=str(user_account.learner_id),
        email=clean_email,
        display_name=user_account.display_name,
    )


@router.post(
    "/logout",
    summary="Invalidate session and clear session cookie",
)
async def logout_user(response: Response) -> dict[str, str]:
    """Clear HttpOnly session cookie."""
    response.delete_cookie(key="session_id", path="/")
    return {"status": "logged_out"}


@router.get(
    "/me",
    response_model=AuthUserResponse,
    summary="Get current authenticated user identity",
)
async def get_current_user_me(
    current_user: UserAccount = Depends(get_current_user_account),
) -> AuthUserResponse:
    """Return user_id, learner_id, email, display_name for authenticated session. Never returns password_hash."""
    return AuthUserResponse(
        user_id=str(current_user.id),
        learner_id=str(current_user.learner_id),
        email=current_user.email,
        display_name=current_user.display_name,
    )

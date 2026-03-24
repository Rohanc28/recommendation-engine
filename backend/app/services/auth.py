from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    stmt = select(User).where(User.id == user_id, User.is_active == True)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise credentials_exc
    return user


async def get_current_user_optional(
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    return (await db.execute(stmt)).scalar_one_or_none()

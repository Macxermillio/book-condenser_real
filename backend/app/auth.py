# app/auth.py

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from supabase import Client

from app.db import get_supabase
from app.core.logging import logger
from app.exceptions.auth import AuthenticationError, InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase: Client = Depends(get_supabase),
):
    try:
        user = supabase.auth.get_user(token)
    except Exception as e:
        raise AuthenticationError(
            log_message=f"Supabase auth failure: {e}"
        ) from e

    if not user or not user.user:
        raise InvalidTokenError()

    logger.info("Authenticated user: %s", user.user.id)
    return user.user

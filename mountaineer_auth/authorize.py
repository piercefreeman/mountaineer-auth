from datetime import datetime, timedelta, timezone
from typing import TypeVar
from uuid import uuid4

from fastapi.responses import Response
from jose import jwt

from mountaineer_auth import dependencies as AuthDependencies
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import UserAuthMixin

ResponseType = TypeVar("ResponseType", bound=Response)


def authorize_response(
    response: ResponseType,
    *,
    user: UserAuthMixin,
    auth_config: AuthConfig,
    token_expiration_minutes: int | None = None,
) -> ResponseType:
    """
    Adds a cookie to the passed response that authorizes the given
    user via a session cookie.
    """
    resolved_token_expiration_minutes = (
        token_expiration_minutes
        if token_expiration_minutes is not None
        else auth_config.AUTH_LOGIN_EXPIRATION_MINUTES
    )

    access_token = authorize_user(
        user=user,
        auth_config=auth_config,
        token_expiration_minutes=resolved_token_expiration_minutes,
    )

    response.set_cookie(
        key=AuthDependencies.access_token_cookie_key(),
        value=f"Bearer {access_token}",
        httponly=True,
        # secure=True,  # Set to False if you're testing locally without HTTPS
        secure=False,
        samesite="lax",  # Helps with CSRF protection
        # The cookie max age needs to be set, even with the separate JIT expiration
        # otherwise browsers will default it to a session cookie that expires when
        # the browser is closed.
        max_age=resolved_token_expiration_minutes * 60,
    )
    return response


def authorize_user(
    *,
    user: UserAuthMixin,
    auth_config: AuthConfig,
    token_expiration_minutes: int | None = None,
):
    """
    Generates a temporary API key bound to the authenticated user's version.
    Pass the same user snapshot used to verify the password.

    """
    # Randomly seed with a uuid4, then encrypt with our secret key to add
    # more entropy to the tokens and make it harder to brute-force the raw token ID
    resolved_token_expiration_minutes = (
        token_expiration_minutes
        if token_expiration_minutes is not None
        else auth_config.AUTH_LOGIN_EXPIRATION_MINUTES
    )
    raw_token = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=resolved_token_expiration_minutes
    )
    to_encode = {
        "sub": str(raw_token),
        "user_id": str(user.id),
        "auth_version": user.auth_version,
        "exp": expire,
    }
    encoded_token = jwt.encode(
        to_encode,
        auth_config.API_SECRET_KEY,
        algorithm=auth_config.API_KEY_ALGORITHM,
    )

    return encoded_token

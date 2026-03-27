from datetime import datetime, timedelta, timezone
from typing import TypeVar
from uuid import UUID, uuid4

from fastapi.responses import Response
from jose import jwt

from mountaineer_auth import dependencies as AuthDependencies
from mountaineer_auth.config import AuthConfig

ResponseType = TypeVar("ResponseType", bound=Response)


def authorize_response(
    response: ResponseType,
    *,
    user_id: UUID,
    auth_config: AuthConfig,
    token_expiration_minutes: int,
) -> ResponseType:
    """
    Adds a cookie to the passed response that authorizes the given
    user via a session cookie.
    """
    access_token = authorize_user(
        user_id=user_id,
        auth_config=auth_config,
        token_expiration_minutes=token_expiration_minutes,
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
        max_age=token_expiration_minutes * 60,
    )
    return response


def authorize_user(
    *,
    user_id: UUID,
    auth_config: AuthConfig,
    token_expiration_minutes: int,
):
    """
    Generates the user a new temporary API key

    """
    # Randomly seed with a uuid4, then encrypt with our secret key to add
    # more entropy to the tokens and make it harder to brute-force the raw token ID
    raw_token = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=token_expiration_minutes)
    to_encode = {"sub": str(raw_token), "user_id": str(user_id), "exp": expire}
    encoded_token = jwt.encode(
        to_encode,
        auth_config.API_SECRET_KEY,
        algorithm=auth_config.API_KEY_ALGORITHM,
    )

    return encoded_token

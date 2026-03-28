from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies
from jose import ExpiredSignatureError, JWTError, jwt

from mountaineer import CoreDependencies

from mountaineer_auth.config import AuthConfig
from mountaineer_auth.exceptions import UnauthorizedError
from mountaineer_auth.logging import LOGGER
from mountaineer_auth.models import UserAuthMixin


def peek_user_id(
    request: Request,
    auth_config: AuthConfig = Depends(
        CoreDependencies.get_config_with_type(AuthConfig)
    ),
) -> UUID | None:
    """
    Extracts and validates the user ID from the JWT token in the request cookies.
    Does not raise exceptions on invalid tokens, making it safe for optional auth flows.

    :param request: The FastAPI request object containing cookies
    :param auth_config: Auth configuration containing API keys and algorithms
    :return: The validated user ID if present and valid, None otherwise

    Returns None in cases of:
        * Missing token
        * Expired token
        * Invalid token format
        * Missing user_id in payload
    """
    try:
        token = request.cookies.get(access_token_cookie_key())
        if not token:
            return None

        token = token.lstrip("Bearer").strip()
        payload = jwt.decode(
            token,
            auth_config.API_SECRET_KEY,
            algorithms=[auth_config.API_KEY_ALGORITHM],
        )

        user_id = payload.get("user_id")
        if user_id is None:
            return None

        return UUID(user_id)
    except ExpiredSignatureError:
        LOGGER.exception("Token expired")
        return None
    except JWTError as e:
        LOGGER.exception(e)
        return None


async def peek_user(
    request: Request,
    user_id: UUID | None = Depends(peek_user_id),
    auth_config: AuthConfig = Depends(
        CoreDependencies.get_config_with_type(AuthConfig)
    ),
    db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
) -> UserAuthMixin | None:
    """
    Retrieves the full user object from the database based on the authenticated user ID.
    This is a non-throwing dependency suitable for optional auth flows.

    :param request: The FastAPI request object
    :param user_id: Optional UUID from the JWT token validation
    :param auth_config: Auth configuration containing user model information
    :param db_connection: Database connection for querying the user
    :return: The full user object if found, None if the user_id is invalid or the user doesn't exist
    """
    # If user_id is none we failed validation of the user credentials
    if user_id is None:
        return None

    user_query = select(auth_config.AUTH_USER).where(
        auth_config.AUTH_USER.id == user_id
    )
    users = await db_connection.exec(user_query)
    return users[0] if users else None


def require_valid_user_id(
    user_id: UUID | None = Depends(peek_user_id),
) -> UUID:
    """
    Enforces that a valid user ID is present in the request.
    Unlike peek_user_id, this dependency will raise an UnauthorizedError if no valid user ID exists.

    :param user_id: Optional UUID from the JWT token validation
    :return: The validated user ID
    :raises UnauthorizedError: If no valid user ID is present
    """
    if user_id is None:
        raise UnauthorizedError()

    return user_id


def require_valid_user(
    peeked_user: UserAuthMixin | None = Depends(peek_user),
) -> UserAuthMixin:
    """
    Enforces that a valid user object exists for the request.
    This combines database validation with token validation.

    :param peeked_user: Optional user object from the database
    :return: The validated user object
    :raises UnauthorizedError: If no valid user exists or cannot be found in the database
    """
    if peeked_user is None:
        raise UnauthorizedError()

    return peeked_user


def require_admin_user(
    user: UserAuthMixin = Depends(require_valid_user),
) -> UserAuthMixin:
    """
    Enforces that the authenticated user has admin privileges.
    This should be used to protect admin-only endpoints.

    :param user: The validated user object
    :return: The validated admin user object
    :raises HTTPException: With 403 status if the user is not an admin
    :raises UnauthorizedError: If no valid user exists (inherited from require_valid_user)
    """
    if not user.is_admin:
        # The user's logged in but they're not an admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return user


def access_token_cookie_key() -> str:
    """
    Returns the standardized cookie key used for storing the JWT access token.

    :return: The cookie key name 'access_key'
    """
    return "access_key"

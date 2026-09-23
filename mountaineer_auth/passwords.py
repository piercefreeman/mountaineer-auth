from iceaxe import DBConnection, select, update

from mountaineer_auth.config import AuthConfig
from mountaineer_auth.exceptions import UnauthorizedError
from mountaineer_auth.models import UserAuthMixin, VerificationType


async def change_password(
    *,
    user: UserAuthMixin,
    password: str,
    auth_config: AuthConfig,
    db_connection: DBConnection,
) -> UserAuthMixin:
    """Persist a password and revoke all credentials and outstanding reset links.

    Call only after authorizing the change (current-password verification or
    validated recovery). Pass the user snapshot used for that authorization.
    Returns the updated user; the original snapshot is no longer authorized.
    """
    hashed_password = auth_config.AUTH_USER.get_password_hash(password)
    async with db_connection.transaction(ensure=True):
        users = await db_connection.exec(
            select(auth_config.AUTH_USER)
            .where(auth_config.AUTH_USER.id == user.id)
            .for_update()
        )
        current_user = users[0] if users else None
        if current_user is None or current_user.auth_version != user.auth_version:
            raise UnauthorizedError()

        current_user.hashed_password = hashed_password
        current_user.auth_version += 1
        await db_connection.update([current_user])

        verification_model = auth_config.AUTH_VERIFICATION_STATE
        await db_connection.exec(
            update(verification_model)
            .set(verification_model.is_used, True)
            .where(
                verification_model.user_id == user.id,
                verification_model.verification_type
                == VerificationType.FORGOT_PASSWORD,
                verification_model.is_used == False,  # noqa: E712 - SQL predicate
            )
        )
    return current_user

from datetime import datetime, timezone
from typing import Awaitable, Callable

from fastapi import Depends
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies
from pydantic import BaseModel

from mountaineer import (
    APIException,
    ControllerBase,
    CoreDependencies,
    LinkAttribute,
    ManagedViewPath,
    Metadata,
    RenderBase,
    ViewportMeta,
    passthrough,
)

from mountaineer_auth import models
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import VerificationType
from mountaineer_auth.views import get_auth_view_path


class VerifyRender(RenderBase):
    not_found: bool = False
    expired: bool = False
    is_used: bool = False
    success: bool = False

    verification_code: str
    verification_type: VerificationType


class ResetPasswordRequest(BaseModel):
    password: str
    verify_password: str


class ResetPasswordInvalid(APIException):
    status_code = 401
    invalid_reason: str


class VerifyController(ControllerBase):
    """
    Email->service verification endpoint if email verifications are enabled.

    Used for both the initial user verification and for password reset flows.

    """

    url = "/auth/verify"
    view_path = (
        ManagedViewPath.from_view_root(get_auth_view_path(""), package_root_link=None)
        / "auth/verify/page.tsx"
    )

    def __init__(
        self,
        reset_password_callback: Callable[[str], Awaitable[None]] | None = None,
    ):
        super().__init__()
        self.reset_password_callback = reset_password_callback

    async def render(
        self,
        verification_code: str,
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
        config: AuthConfig = Depends(CoreDependencies.get_config_with_type(AuthConfig)),
    ) -> VerifyRender:
        verification_state = await self.get_verification_obj(
            verification_code=verification_code,
            db_connection=db_connection,
            config=config,
        )

        verify_model = VerifyRender(
            verification_code=verification_code,
            verification_type=(
                verification_state.verification_type
                if verification_state
                # Arbitrary verification type, the frontend will handle by throwing
                # an error that we can't find this instance
                else VerificationType.INITIAL
            ),
            metadata=Metadata(
                title="Email Verification",
                links=[
                    LinkAttribute(
                        rel="stylesheet", href=f"{self._scripts_prefix}/auth_main.css"
                    ),
                ],
                metas=[ViewportMeta()],
                ignore_global_metadata=True,
            ),
        )

        if verification_state is None:
            return verify_model.model_copy(update={"not_found": True})

        if verification_state.expiration_date < datetime.now(timezone.utc):
            return verify_model.model_copy(update={"expired": True})

        if verification_state.is_used:
            return verify_model.model_copy(update={"is_used": True})

        # The initial verification of a user doesn't require any actions on the page. Just
        # accessing the page should verify the user.
        if verification_state.verification_type == VerificationType.INITIAL:
            await self.verify_initial_user(
                config=config,
                verification_state=verification_state,
                db_connection=db_connection,
            )

        return verify_model.model_copy(update={"success": True})

    @passthrough(exception_models=[ResetPasswordInvalid])
    async def reset_password(
        self,
        verification_code: str,
        payload: ResetPasswordRequest,
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
        config: AuthConfig = Depends(CoreDependencies.get_config_with_type(AuthConfig)),
    ) -> None:
        verification_state = await self.get_verification_obj(
            verification_code=verification_code,
            db_connection=db_connection,
            config=config,
        )

        if not verification_state:
            raise ResetPasswordInvalid(invalid_reason="Invalid reset token.")

        # Only allow verification on certain request types
        if verification_state.verification_type != VerificationType.FORGOT_PASSWORD:
            raise ResetPasswordInvalid(invalid_reason="Non-reset password token found.")

        if verification_state.is_used:
            raise ResetPasswordInvalid(
                invalid_reason="Reset token has already been used."
            )

        # Verify passwords are equal
        if payload.password != payload.verify_password:
            raise ResetPasswordInvalid(
                invalid_reason="Passwords are not equal. Re-enter them to make sure they're the same."
            )

        # We can reuse the user identification logic, since forgetting the password
        # is another way to verify the user's email
        hashed_password = config.AUTH_USER.get_password_hash(payload.password)

        user = await self.verify_initial_user(
            config=config,
            verification_state=verification_state,
            db_connection=db_connection,
        )
        user.hashed_password = hashed_password
        await db_connection.update([user])

        if self.reset_password_callback:
            await self.reset_password_callback(verification_code)

    async def verify_initial_user(
        self,
        *,
        config: AuthConfig,
        verification_state: models.VerificationState,
        db_connection: DBConnection,
    ) -> models.UserAuthMixin:
        users = await db_connection.exec(
            select(config.AUTH_USER).where(
                config.AUTH_USER.id == verification_state.user_id,
            )
        )
        user = users[0] if users else None
        if not user:
            raise ValueError("User not found")
        user.is_verified = True
        verification_state.is_used = True
        await db_connection.update([user, verification_state])

        return user

    async def get_verification_obj(
        self,
        *,
        verification_code: str,
        config: AuthConfig,
        db_connection: DBConnection,
    ):
        # Try to find the passed verification code
        verification_state_query = select(config.AUTH_VERIFICATION_STATE).where(
            config.AUTH_VERIFICATION_STATE.code == verification_code
        )
        verification_states = await db_connection.exec(verification_state_query)
        return verification_states[0] if verification_states else None

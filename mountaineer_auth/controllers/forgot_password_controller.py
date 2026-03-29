from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Awaitable, Callable, Type
from uuid import uuid4

from fastapi import Depends
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies
from pydantic import BaseModel

from mountaineer import (
    ControllerBase,
    CoreDependencies,
    LinkAttribute,
    ManagedViewPath,
    Metadata,
    RenderBase,
    ViewportMeta,
    passthrough,
)

from mountaineer_auth.compat import send_email_workflow
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import VerificationType
from mountaineer_auth.views import get_auth_view_path

# During type checking, force the import
if TYPE_CHECKING:
    from mountaineer_auth.emails.forgot_password_email import (
        ForgotPasswordEmailController,
        ForgotPasswordEmailRequest,
    )

# Allow this package to be imported by the __init__ package
# for ease of import, regardless of whether or not this endpoint
# is enabled. If it is enabled, the client project needs to support
# sending emails.
try:
    from mountaineer_auth.emails.forgot_password_email import (
        ForgotPasswordEmailController,
        ForgotPasswordEmailRequest,
    )
except ImportError:
    pass


class ForgotPasswordRender(RenderBase):
    success: bool


class ForgotPasswordRequest(BaseModel):
    username: str


class ForgotPasswordController(ControllerBase):
    url = "/auth/forgot_password"
    view_path = (
        ManagedViewPath.from_view_root(get_auth_view_path(""), package_root_link=None)
        / "auth/forgot_password/page.tsx"
    )

    def __init__(
        self,
        email_controller: Type["ForgotPasswordEmailController"] | None = None,
        email_request: Type["ForgotPasswordEmailRequest"] | None = None,
        verification_expiration_minutes: int = 15,
        forgot_password_callback: Callable[[ForgotPasswordRequest], Awaitable[None]]
        | None = None,
    ):
        """
        :param verification_expiration_minutes: Short duration to prevent abuse
        """
        super().__init__()
        self.email_controller = email_controller
        self.email_request = email_request
        self.verification_expiration_minutes = verification_expiration_minutes
        self.forgot_password_callback = forgot_password_callback

    async def render(
        self,
        success: bool = False,
        config: AuthConfig = Depends(CoreDependencies.get_config_with_type(AuthConfig)),
    ) -> ForgotPasswordRender:
        # We require emails to support password resets
        if not config.AUTH_EMAIL_ENABLED:
            raise ValueError("Emails are not enabled")

        return ForgotPasswordRender(
            success=success,
            metadata=Metadata(
                title="Forgot Password",
                links=[
                    LinkAttribute(
                        rel="stylesheet", href=f"{self._scripts_prefix}/auth_main.css"
                    ),
                ],
                metas=[ViewportMeta()],
                ignore_global_metadata=True,
            ),
        )

    @passthrough
    async def forgot_password(
        self,
        login_payload: ForgotPasswordRequest,
        config: AuthConfig = Depends(CoreDependencies.get_config_with_type(AuthConfig)),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> None:
        """
        Resetting password shouldn't leak information about active user accounts. As such
        we return a successful response regardless of whether the user exists or not.

        """
        if not config.AUTH_EMAIL_ENABLED or not config.AUTH_EMAIL:
            raise ValueError("Emails are not enabled")

        email_controller = self.email_controller or ForgotPasswordEmailController
        email_request = self.email_request or ForgotPasswordEmailRequest

        user_model = config.AUTH_USER
        matched_users = select(user_model).where(
            user_model.email == login_payload.username
        )
        users = await db_connection.exec(matched_users)
        user = users[0] if users else None

        if user is not None:
            verification_code = config.AUTH_VERIFICATION_STATE(
                code=self.get_verification_code(),
                expiration_date=(
                    datetime.now(timezone.utc)
                    + timedelta(minutes=self.verification_expiration_minutes)
                ),
                user_id=user.id,
                verification_type=VerificationType.FORGOT_PASSWORD,
            )
            await db_connection.insert([verification_code])

            # Send the password reset email
            await send_email_workflow(
                email_controller,
                email_request(
                    verification_host=config.AUTH_EMAIL.server_host,
                    verification_code=verification_code.code,
                    user_id=user.id,
                ),
                to_email=user.email,
                from_email=str(config.AUTH_EMAIL.from_email),
                from_name=config.AUTH_EMAIL.from_name or config.AUTH_EMAIL.project_name,
            )

        if self.forgot_password_callback:
            await self.forgot_password_callback(login_payload)

    def get_verification_code(self) -> str:
        return str(uuid4())

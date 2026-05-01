from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Awaitable, Callable, Type
from uuid import uuid4

from fastapi import Depends, status
from fastapi.responses import JSONResponse
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies
from pydantic import BaseModel, EmailStr

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

from mountaineer_email.registry import SerializedEmailController
from mountaineer_email.workflows.send_email import SendEmail, SendEmailInput

from mountaineer_auth import models
from mountaineer_auth.authorize import authorize_response
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import VerificationType
from mountaineer_auth.views import get_auth_view_path

if TYPE_CHECKING:
    from mountaineer_auth.emails.verify_email import (
        VerifyEmailController,
        VerifyEmailRequest,
    )

try:
    from mountaineer_auth.emails.verify_email import (
        VerifyEmailController,
        VerifyEmailRequest,
    )
except ImportError:
    pass


class SignupRender(RenderBase):
    post_signup_redirect: str


class SignupRequest(BaseModel):
    username: EmailStr
    password: str


class SignupInvalid(APIException):
    status_code = 401
    invalid_reason: str


class SignupController(ControllerBase):
    url = "/auth/signup"
    view_path = (
        ManagedViewPath.from_view_root(get_auth_view_path(""), package_root_link=None)
        / "auth/signup/page.tsx"
    )

    def __init__(
        self,
        post_signup_redirect: str = "/",
        verify_email_controller: Type["VerifyEmailController"] | None = None,
        verify_email_request: Type["VerifyEmailRequest"] | None = None,
        token_expiration_minutes: int | None = None,
        verification_expiration_minutes: int = 60 * 24,
        signup_callback: Callable[[SignupRequest], Awaitable[None]] | None = None,
    ):
        """
        :param token_expiration_minutes: Defaults to auth_config.AUTH_LOGIN_EXPIRATION_MINUTES
        :param verification_expiration_minutes: Defaults to 24 hours

        """
        super().__init__()
        self.post_signup_redirect = post_signup_redirect
        self.verify_email_controller = verify_email_controller
        self.verify_email_request = verify_email_request
        self.token_expiration_minutes = token_expiration_minutes
        self.verification_expiration_minutes = verification_expiration_minutes
        self.signup_callback = signup_callback

    def render(
        self,
        auth_config: AuthConfig = Depends(
            CoreDependencies.get_config_with_type(AuthConfig)
        ),
    ) -> SignupRender:
        return SignupRender(
            post_signup_redirect=self.post_signup_redirect,
            metadata=Metadata(
                title="Signup",
                links=[
                    LinkAttribute(
                        rel="stylesheet", href=f"{self._scripts_prefix}/auth_main.css"
                    ),
                ],
                metas=[ViewportMeta()],
                ignore_global_metadata=True,
            ),
        )

    @passthrough(exception_models=[SignupInvalid])
    async def signup(
        self,
        signup_payload: SignupRequest,
        auth_config: AuthConfig = Depends(
            CoreDependencies.get_config_with_type(AuthConfig)
        ),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> JSONResponse:
        matched_users = select(auth_config.AUTH_USER).where(
            auth_config.AUTH_USER.email == signup_payload.username
        )
        users = await db_connection.exec(matched_users)
        user = users[0] if users else None
        if user is not None:
            raise SignupInvalid(invalid_reason="User already exists with this email.")

        # Create a new user
        hashed_password = auth_config.AUTH_USER.get_password_hash(
            signup_payload.password
        )

        new_user = await self.build_user(
            auth_config.AUTH_USER, signup_payload.username, hashed_password
        )
        await db_connection.insert([new_user])

        # Send out a verification email
        if auth_config.AUTH_EMAIL_ENABLED and auth_config.AUTH_EMAIL:
            verify_email_controller = (
                self.verify_email_controller or VerifyEmailController
            )
            verify_email_request = self.verify_email_request or VerifyEmailRequest

            verification_code = auth_config.AUTH_VERIFICATION_STATE(
                code=self.get_verification_code(),
                expiration_date=(
                    datetime.now(timezone.utc)
                    + timedelta(minutes=self.verification_expiration_minutes)
                ),
                user_id=new_user.id,
                verification_type=VerificationType.INITIAL,
            )
            await db_connection.insert([verification_code])

            # Send the verification email
            send_email_input = SendEmailInput(
                email_controller=verify_email_controller,
                email_input=verify_email_request(
                    verification_code=verification_code.code,
                    verification_host=auth_config.AUTH_EMAIL.server_host,
                    user_id=new_user.id,
                ),
                to_email=new_user.email,
                from_email=str(auth_config.AUTH_EMAIL.from_email),
                from_name=auth_config.AUTH_EMAIL.from_name
                or auth_config.AUTH_EMAIL.project_name,
            )
            if not isinstance(
                send_email_input.email_controller,
                SerializedEmailController,
            ):
                raise TypeError("Email controller must serialize before workflow run")

            await SendEmail().run(
                email_controller=send_email_input.email_controller,
                email_input=send_email_input.email_input,
                to_email=str(send_email_input.to_email),
                to_name=send_email_input.to_name,
                from_email=str(send_email_input.from_email),
                from_name=send_email_input.from_name,
            )

        response = JSONResponse(content=[], status_code=status.HTTP_200_OK)
        response = authorize_response(
            response,
            user_id=new_user.id,
            auth_config=auth_config,
            token_expiration_minutes=self.token_expiration_minutes,
        )

        if self.signup_callback:
            await self.signup_callback(signup_payload)

        return response

    def get_verification_code(self) -> str:
        return str(uuid4())

    async def build_user(
        self, model: Type[models.UserAuthMixin], username: str, hashed_password: str
    ):
        return model(
            # Normalize the email address, matches the login validation
            email=username.lower().strip(),
            hashed_password=hashed_password,
        )

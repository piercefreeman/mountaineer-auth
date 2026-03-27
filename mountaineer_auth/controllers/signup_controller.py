from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Awaitable, Callable, Type
from uuid import uuid4

from fastapi import Depends, Request, status
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

from mountaineer_auth import models
from mountaineer_auth.authorize import authorize_response
from mountaineer_auth.compat import send_email_workflow
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import VerificationType
from mountaineer_auth.recaptcha import validate_recaptcha
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
    recaptcha_enabled: bool
    recaptcha_client_key: str | None
    recaptcha_action: str


class SignupRequest(BaseModel):
    username: EmailStr
    password: str
    recaptcha_key: str | None


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
        token_expiration_minutes: int = 60 * 24,
        verification_expiration_minutes: int = 60 * 24,
        signup_callback: Callable[[SignupRequest], Awaitable[None]] | None = None,
    ):
        """
        :param token_expiration_minutes: Defaults to 24 hours
        :param verification_expiration_minutes: Defaults to 24 hours

        """
        super().__init__()
        self.post_signup_redirect = post_signup_redirect
        self.recaptcha_action = "signup"
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
            recaptcha_enabled=auth_config.RECAPTCHA_ENABLED,
            recaptcha_client_key=(
                auth_config.RECAPTCHA.gcp_client_key if auth_config.RECAPTCHA else None
            ),
            recaptcha_action=self.recaptcha_action,
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
        request: Request,
        signup_payload: SignupRequest,
        auth_config: AuthConfig = Depends(
            CoreDependencies.get_config_with_type(AuthConfig)
        ),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> JSONResponse:
        # If recapcha is enabled, we require the key
        if auth_config.RECAPTCHA_ENABLED:
            if signup_payload.recaptcha_key is None:
                raise SignupInvalid(invalid_reason="Recaptcha is required.")

            # Validate recaptcha key only if enabled; otherwise we will be unable to create
            # the client because the GCP configuration values will be missing
            # This will raise a RecaptchaValidationError if it fails, which will short-circuit
            # this logic and return a generic error to the client
            await validate_recaptcha(
                signup_payload.recaptcha_key,
                self.recaptcha_action,
            )

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
            await send_email_workflow(
                verify_email_controller,
                verify_email_request(
                    verification_code=verification_code.code,
                    verification_host=auth_config.AUTH_EMAIL.server_host,
                    user_id=new_user.id,
                ),
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

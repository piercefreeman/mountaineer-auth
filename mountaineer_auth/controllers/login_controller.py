from typing import Awaitable, Callable

from fastapi import Depends, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
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

from mountaineer_auth import dependencies as AuthDependencies
from mountaineer_auth.authorize import authorize_response
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import UserAuthMixin
from mountaineer_auth.views import get_auth_view_path


class LoginRequest(BaseModel):
    username: EmailStr
    password: str


class LoginInvalid(APIException):
    status_code = 401
    invalid_reason: str


class LoginRender(RenderBase):
    post_login_redirect: str
    include_signup_link: bool


class LoginController(ControllerBase):
    """
    Clients can override this login controller to instantiate their own login / view conventions.
    """

    url = "/auth/login"
    view_path = (
        ManagedViewPath.from_view_root(get_auth_view_path(""), package_root_link=None)
        / "auth/login/page.tsx"
    )

    def __init__(
        self,
        post_login_redirect: str = "/",
        include_signup_link: bool = True,
        token_expiration_minutes: int = 60 * 24,
        login_callback: Callable[[LoginRequest], Awaitable[None]] | None = None,
    ):
        """
        :param token_expiration_minutes: Defaults to 24 hours

        """
        super().__init__()
        self.post_login_redirect = post_login_redirect
        self.include_signup_link = include_signup_link
        self.token_expiration_minutes = token_expiration_minutes
        self.login_callback = login_callback

    async def render(
        self,
        request: Request,
        after_login: str | None = None,
        user: UserAuthMixin | None = Depends(AuthDependencies.peek_user),
    ) -> LoginRender:
        if user is not None:
            # return RedirectResponse(url=self.post_login_redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
            return LoginRender(
                post_login_redirect="",
                include_signup_link=self.include_signup_link,
                metadata=Metadata(
                    explicit_response=RedirectResponse(
                        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                        url=after_login or self.post_login_redirect,
                    )
                ),
            )

        # Otherwise continue to load the initial page
        return LoginRender(
            post_login_redirect=after_login or self.post_login_redirect,
            include_signup_link=self.include_signup_link,
            metadata=Metadata(
                title="Login",
                links=[
                    LinkAttribute(
                        rel="stylesheet", href=f"{self._scripts_prefix}/auth_main.css"
                    ),
                ],
                metas=[ViewportMeta()],
                ignore_global_metadata=True,
            ),
        )

    @passthrough(exception_models=[LoginInvalid])
    async def login(
        self,
        login_payload: LoginRequest,
        auth_config: AuthConfig = Depends(
            CoreDependencies.get_config_with_type(AuthConfig)
        ),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> JSONResponse:
        user_model = auth_config.AUTH_USER
        matched_users = select(user_model).where(
            user_model.email == login_payload.username.strip().lower()
        )
        users = await db_connection.exec(matched_users)
        user = users[0] if users else None
        if user is None:
            raise LoginInvalid(invalid_reason="User not found.")
        if not user.verify_password(login_payload.password):
            raise LoginInvalid(invalid_reason="Invalid password.")

        response = JSONResponse(content=[], status_code=status.HTTP_200_OK)
        response = authorize_response(
            response,
            user_id=user.id,
            auth_config=auth_config,
            token_expiration_minutes=self.token_expiration_minutes,
        )

        if self.login_callback:
            await self.login_callback(login_payload)

        return response

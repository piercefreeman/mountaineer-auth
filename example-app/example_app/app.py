from urllib.parse import urlencode

from fastapi import Request, status
from fastapi.responses import RedirectResponse
from iceaxe import DBConnection
from iceaxe.mountaineer import DatabaseDependencies
from mountaineer_email.plugin import plugin as email_plugin

from mountaineer import AppController, Depends
from mountaineer.client_compiler.postcss import PostCSSBundler
from mountaineer.dependencies import get_function_dependencies
from mountaineer.render import LinkAttribute, Metadata

from example_app.bootstrap import bootstrap_database
from example_app.config import AppConfig
from example_app.controllers import DetailController, HomeController
from example_app.emails import WelcomePreviewEmail
from mountaineer_auth import (
    create_plugin as create_auth_plugin,
    ForgotPasswordController,
    LoginController,
    LogoutController,
    SignupController,
    UnauthorizedError,
    VerifyController,
)

app_config = AppConfig()

controller = AppController(
    config=app_config,
    global_metadata=Metadata(
        links=[LinkAttribute(rel="stylesheet", href="/static/app_main.css")],
    ),
    custom_builders=[
        PostCSSBundler(),
    ],
)

auth_plugin = create_auth_plugin()
auth_plugin.init_controller(ForgotPasswordController())
auth_plugin.init_controller(LoginController(post_login_redirect="/"))
auth_plugin.init_controller(SignupController(post_signup_redirect="/"))
auth_plugin.init_controller(LogoutController(post_logout_redirect="/"))
auth_plugin.init_controller(VerifyController())

controller.register(HomeController())
controller.register(DetailController())
controller.register(auth_plugin)
controller.register(WelcomePreviewEmail())
controller.register(email_plugin)


@controller.app.on_event("startup")
async def ensure_example_data() -> None:
    # Bootstrap the schema and a single protected record so the POC works on first run.
    async def _bootstrap(
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> None:
        await bootstrap_database(db_connection)

    async with get_function_dependencies(callable=_bootstrap) as deps:
        await _bootstrap(**deps)


async def handle_unauthorized(
    request: Request,
    exc: UnauthorizedError,
) -> RedirectResponse:
    _ = exc
    return RedirectResponse(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        url=f"/auth/login?{urlencode({'after_login': str(request.url)})}",
    )


controller.app.exception_handler(UnauthorizedError)(handle_unauthorized)

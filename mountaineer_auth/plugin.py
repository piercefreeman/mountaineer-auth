from typing import cast

from mountaineer.client_compiler.postcss import PostCSSBundler
from mountaineer.plugin import CONTROLLER_TYPE, BuildConfig, MountaineerPlugin

from mountaineer_auth import controllers, emails
from mountaineer_auth.views import get_auth_view_path

AUTH_PLUGIN_CONTROLLERS = cast(
    list[type[CONTROLLER_TYPE]],
    [
        controllers.ForgotPasswordController,
        controllers.LoginController,
        controllers.LogoutController,
        controllers.SignupController,
        controllers.VerifyController,
        emails.ForgotPasswordEmailController,
        emails.VerifyEmailController,
    ],
)


def create_plugin() -> MountaineerPlugin:
    return MountaineerPlugin(
        name="mountaineer-auth",
        controllers=AUTH_PLUGIN_CONTROLLERS,
        view_root=get_auth_view_path(""),
        build_config=BuildConfig(custom_builders=[PostCSSBundler()]),
    )


plugin = create_plugin()

from mountaineer.client_compiler.postcss import PostCSSBundler
from mountaineer.plugin import BuildConfig, MountaineerPlugin

from mountaineer_auth import controllers, emails
from mountaineer_auth.views import get_auth_view_path

plugin = MountaineerPlugin(
    name="mountaineer-auth",
    controllers=[
        controllers.ForgotPasswordController,
        controllers.LoginController,
        controllers.LogoutController,
        controllers.SignupController,
        controllers.VerifyController,
        emails.ForgotPasswordEmailController,
        emails.VerifyEmailController,
    ],
    view_root=get_auth_view_path(""),
    build_config=BuildConfig(custom_builders=[PostCSSBundler()]),
)

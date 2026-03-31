from mountaineer_auth import dependencies as AuthDependencies  # noqa: F401
from mountaineer_auth.config import (
    AuthConfig as AuthConfig,
    AuthEmailConfig as AuthEmailConfig,
)
from mountaineer_auth.controllers.forgot_password_controller import (
    ForgotPasswordController as ForgotPasswordController,
)
from mountaineer_auth.controllers.login_controller import (
    LoginController as LoginController,
)
from mountaineer_auth.controllers.logout_controller import (
    LogoutController as LogoutController,
)
from mountaineer_auth.controllers.signup_controller import (
    SignupController as SignupController,
)
from mountaineer_auth.controllers.verify_controller import (
    VerifyController as VerifyController,
)
from mountaineer_auth.exceptions import UnauthorizedError as UnauthorizedError
from mountaineer_auth.models import UserAuthMixin as UserAuthMixin
from mountaineer_auth.plugin import (
    create_plugin as create_plugin,
    plugin as plugin,
)
from mountaineer_auth.workflows import (
    SendAuthEmail as SendAuthEmail,
    SendAuthEmailInput as SendAuthEmailInput,
    SendAuthEmailResult as SendAuthEmailResult,
)

SendEmail = SendAuthEmail
SendEmailInput = SendAuthEmailInput

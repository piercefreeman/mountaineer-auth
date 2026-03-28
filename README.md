# mountaineer-auth

This is a opinionated login package you can use to get up and running asap with a [Mountaineer](https://github.com/piercefreeman/mountaineer) webapp.

1. `User` Base Model
2. Sign up page with email and password
3. Login page with email and password
4. JWT token generation and validation

## Getting Started

Add the models to a file like `models/auth.py`:

```python
from mountaineer_auth.models import (
    UserAuthMixin,
)
from mountaineer_auth.models import (
    VerificationState as VerificationStateBase,
)

class User(UserAuthMixin):
    pass

class VerificationState(VerificationStateBase):
    pass
```

Add the controllers to your app.py:

```python
from fastapi import Request, status
from fastapi.responses import RedirectResponse

from mountaineer_auth import controllers as auth_controllers
from mountaineer_auth import emails as auth_emails
from mountaineer_auth.exceptions import UnauthorizedError

controller = AppController(...)

controller.register(auth_controllers.LoginController(post_login_redirect="/app"))
controller.register(auth_controllers.SignupController(post_signup_redirect="/app"))
controller.register(auth_controllers.LogoutController(post_logout_redirect="/"))
controller.register(auth_controllers.ForgotPasswordController())
controller.register(auth_controllers.VerifyController())

# Optional, if you want email support
controller.register(auth_emails.VerifyEmailController())
controller.register(auth_emails.ForgotPasswordEmailController())

# If an unauthorized error is thrown in runtime, redirect to the login page
async def handle_unauthorized(request: Request, exc: UnauthorizedError):
    return RedirectResponse(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        url=f"/auth/login?after_login={request.url}",
    )

controller.app.exception_handler(UnauthorizedError)(handle_unauthorized)
```

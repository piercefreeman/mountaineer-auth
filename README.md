# mountaineer-auth

mountaineer-auth is a opinionated login package you can use to get up and running asap with a [Mountaineer](https://github.com/piercefreeman/mountaineer) webapp. It's secure and has been used in the wild for the last two years.

Each _user_ registers with their email and password. _You_ handle appropriate authorization on your routes to determine what user is allowed where. We handle all lifecycle: login, signup, password reset, JWT tokens, etc.

- Beautifully designed registration and login flows
- First-class primitive for admin users
- Dependency injection functions to quickly validate users before they hit your routes
- All self-hosted for fast performance on your infra

## Getting Started

This guide assumes that you're using the full `mountaineer` ecosystem: `iceaxe` for database models, `waymark` for backend workflows, `mountaineer-cloud` for email sending, etc. Add the models to a file like `models/auth.py`:

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

## Testing

`make test` starts a disposable Postgres instance from `docker-compose.test.yml`, runs the pytest suite, and tears the database down afterwards.

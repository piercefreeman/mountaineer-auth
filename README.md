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

## Password changes and credential revocation

Successful password resets invalidate all existing sessions, API JWTs, and
outstanding password-reset links for that account. The owner must sign in again.
Every authentication dependency, including `require_valid_user_id`, checks the
token's `auth_version` against the current database record.

For an application's authenticated password-change flow, verify the current
password and call the shared operation instead of assigning `hashed_password`:

```python
from mountaineer_auth import UnauthorizedError, change_password

if not user.verify_password(current_password):
    raise UnauthorizedError()

updated_user = await change_password(
    user=user,
    password=new_password,
    auth_config=config,
    db_connection=db_connection,
)
```

Pass the authenticated user snapshot; a concurrent password change makes it
invalid. The operation atomically updates the password, increments `auth_version`,
and consumes outstanding reset links. It returns the updated user and revokes
the caller's old session too. Apply the application's password policy before
calling it. Direct assignments to `hashed_password` bypass this revocation.

### Upgrading existing applications

- Add a non-null integer `auth_version` column, backfilled to `0`, to every table
  inheriting `UserAuthMixin` before deploying. For the default table name:
  `ALTER TABLE "user" ADD COLUMN auth_version integer NOT NULL DEFAULT 0;`
  Use the actual table name from your application's model/migrations.
- Update custom token issuers to call `authorize_user(user=user, ...)` and
  `authorize_response(response, user=user, ...)` instead of passing `user_id`.
  Use the same user snapshot that passed password verification; do not reload
  its version after verifying an old password.
- Existing JWTs without `auth_version` are treated as version `0`, preserving
  valid sessions and API JWTs on upgrade. The first password change or reset
  increments the user's version and invalidates those legacy credentials too.
  This does not retroactively revoke tokens for password resets performed before
  the upgrade. Upgrade every service/replica accepting these credentials; older
  validators do not enforce revocation.
- `Depends(...)` usage of authentication dependencies is unchanged. For direct
  Python calls, use `user = await peek_user(request, config, db_connection)` and
  `peek_user_id(user)`. User-ID authentication now requires database access.

## Testing

`make test` starts a disposable Postgres instance from `docker-compose.test.yml`, runs the pytest suite, and tears the database down afterwards.

## Development

If you update the admin UI files, you'll need to build the artifacts for inclusion in the published library. We do this automatically when distributing through CI, so this is just when you're making changes and testing locally:

```bash
uv run build-auth
```

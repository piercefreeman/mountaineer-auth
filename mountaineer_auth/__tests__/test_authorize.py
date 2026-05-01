from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.responses import Response
from jose import jwt

from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.authorize import authorize_response, authorize_user


def test_authorize_user_uses_config_default_expiration(config: models.AppConfig):
    config = config.model_copy(update={"AUTH_LOGIN_EXPIRATION_MINUTES": 30})
    before = datetime.now(timezone.utc)

    token = authorize_user(
        user_id=uuid4(),
        auth_config=config,
    )
    after = datetime.now(timezone.utc)

    claims = jwt.get_unverified_claims(token)
    expire = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)

    assert before + timedelta(minutes=30) - timedelta(seconds=1) <= expire
    assert expire <= after + timedelta(minutes=30) + timedelta(seconds=1)


def test_authorize_user_prefers_explicit_expiration(config: models.AppConfig):
    config = config.model_copy(update={"AUTH_LOGIN_EXPIRATION_MINUTES": 30})
    before = datetime.now(timezone.utc)

    token = authorize_user(
        user_id=uuid4(),
        auth_config=config,
        token_expiration_minutes=5,
    )
    after = datetime.now(timezone.utc)

    claims = jwt.get_unverified_claims(token)
    expire = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)

    assert before + timedelta(minutes=5) - timedelta(seconds=1) <= expire
    assert expire <= after + timedelta(minutes=5) + timedelta(seconds=1)


def test_authorize_response_uses_resolved_expiration_for_cookie(
    config: models.AppConfig,
):
    config = config.model_copy(update={"AUTH_LOGIN_EXPIRATION_MINUTES": 45})
    response = authorize_response(
        Response(),
        user_id=uuid4(),
        auth_config=config,
    )

    set_cookie = response.headers["set-cookie"]

    assert "Max-Age=2700" in set_cookie

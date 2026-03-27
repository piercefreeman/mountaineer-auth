from typing import cast

import pytest
import pytest_asyncio
from fastapi.responses import JSONResponse
from iceaxe import DBConnection

from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.controllers.login_controller import (
    LoginController,
    LoginInvalid,
    LoginRequest,
)


@pytest_asyncio.fixture
async def user_record(
    db_connection: DBConnection,
):
    user = models.User(
        email="myemail@example.com",
        hashed_password=models.User.get_password_hash("mypassword"),
    )
    await db_connection.insert([user])
    return user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password",
    [
        ("myemail@example.com", "mypassword"),
        ("Myemail@example.com", "mypassword"),
        ("myemail@example.com  ", "mypassword"),
    ],
)
async def test_login_success(
    email: str,
    password: str,
    user_record: models.User,
    db_connection: DBConnection,
    config: models.AppConfig,
):
    login_controller = LoginController(post_login_redirect="/")

    response = cast(
        JSONResponse,
        await login_controller.login(
            login_payload=LoginRequest(username=email, password=password),
            auth_config=config,
            db_connection=db_connection,
        ),
    )

    assert response.status_code == 200
    cookies = response.headers.get("set-cookie")
    assert cookies is not None
    assert cookies.startswith('access_key="Bearer ')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password",
    [
        # Wrong email
        ("myemail2@example.com", "mypassword"),
        # Wrong password
        ("myemail@example.com", "mywrongpassword"),
    ],
)
async def test_login_failure(
    email: str,
    password: str,
    user_record: models.User,
    db_connection: DBConnection,
    config: models.AppConfig,
):
    login_controller = LoginController(post_login_redirect="/")

    with pytest.raises(LoginInvalid):
        await login_controller.login(
            login_payload=LoginRequest(username=email, password=password),
            auth_config=config,
            db_connection=db_connection,
        )

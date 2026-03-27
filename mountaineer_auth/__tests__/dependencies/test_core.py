from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException, Request
from iceaxe import DBConnection
from jose import jwt

from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.dependencies.core import (
    access_token_cookie_key,
    peek_user,
    peek_user_id,
    require_admin_user,
    require_valid_user,
    require_valid_user_id,
)
from mountaineer_auth.exceptions import UnauthorizedError


@pytest_asyncio.fixture
async def user_record(db_connection: DBConnection):
    user = models.User(
        email="test@example.com",
        hashed_password=models.User.get_password_hash("password"),
        is_admin=False,
    )
    await db_connection.insert([user])
    return user


@pytest_asyncio.fixture
async def admin_user_record(db_connection: DBConnection):
    user = models.User(
        email="admin@example.com",
        hashed_password=models.User.get_password_hash("password"),
        is_admin=True,
    )
    await db_connection.insert([user])
    return user


@pytest.fixture
def mock_request_with_token(
    config: models.AppConfig, user_record: models.User
) -> Request:
    token = jwt.encode(
        {"user_id": str(user_record.id)},
        config.API_SECRET_KEY,
        algorithm=config.API_KEY_ALGORITHM,
    )
    request = Request({"type": "http"})
    request._cookies = {access_token_cookie_key(): f"Bearer {token}"}
    return request


def test_peek_user_id_success(
    mock_request_with_token: Request,
    config: models.AppConfig,
    user_record: models.User,
):
    user_id = peek_user_id(mock_request_with_token, config)
    assert user_id == user_record.id


def test_peek_user_id_no_token(config: models.AppConfig):
    request = Request({"type": "http", "headers": {}})
    user_id = peek_user_id(request, config)
    assert user_id is None


@pytest.mark.asyncio
async def test_peek_user_success(
    mock_request_with_token: Request,
    config: models.AppConfig,
    db_connection: DBConnection,
    user_record: models.User,
):
    user = await peek_user(
        mock_request_with_token,
        peek_user_id(mock_request_with_token, config),
        config,
        db_connection,
    )
    assert user is not None
    assert user.id == user_record.id
    assert user.email == user_record.email


@pytest.mark.asyncio
async def test_peek_user_not_found(
    mock_request_with_token: Request,
    config: models.AppConfig,
    db_connection: DBConnection,
):
    # Use a random UUID that won't exist in the database
    non_existent_id = uuid4()
    user = await peek_user(
        mock_request_with_token,
        non_existent_id,
        config,
        db_connection,
    )
    assert user is None


def test_require_valid_user_id_success(
    mock_request_with_token: Request,
    config: models.AppConfig,
    user_record: models.User,
):
    user_id = require_valid_user_id(peek_user_id(mock_request_with_token, config))
    assert user_id == user_record.id


def test_require_valid_user_id_failure():
    with pytest.raises(UnauthorizedError):
        require_valid_user_id(None)


@pytest.mark.asyncio
async def test_require_valid_user_success(
    mock_request_with_token: Request,
    config: models.AppConfig,
    db_connection: DBConnection,
    user_record: models.User,
):
    user = require_valid_user(
        await peek_user(
            mock_request_with_token,
            peek_user_id(mock_request_with_token, config),
            config,
            db_connection,
        )
    )
    assert user is not None
    assert user.id == user_record.id


def test_require_valid_user_failure():
    with pytest.raises(UnauthorizedError):
        require_valid_user(None)


@pytest.mark.asyncio
async def test_require_admin_user_success(
    mock_request_with_token: Request,
    config: models.AppConfig,
    db_connection: DBConnection,
    admin_user_record: models.User,
):
    # Create a new token with the admin user
    token = jwt.encode(
        {"user_id": str(admin_user_record.id)},
        config.API_SECRET_KEY,
        algorithm=config.API_KEY_ALGORITHM,
    )
    request = Request({"type": "http"})
    request._cookies = {access_token_cookie_key(): f"Bearer {token}"}

    user = require_admin_user(
        require_valid_user(
            await peek_user(
                request,
                peek_user_id(request, config),
                config,
                db_connection,
            )
        )
    )
    assert user is not None
    assert user.id == admin_user_record.id
    assert user.is_admin is True


@pytest.mark.asyncio
async def test_require_admin_user_failure(
    mock_request_with_token: Request,
    config: models.AppConfig,
    db_connection: DBConnection,
    user_record: models.User,
):
    with pytest.raises(HTTPException) as exc_info:
        require_admin_user(
            require_valid_user(
                await peek_user(
                    mock_request_with_token,
                    peek_user_id(mock_request_with_token, config),
                    config,
                    db_connection,
                )
            )
        )
    assert exc_info.value.status_code == 403


def test_access_token_cookie_key():
    assert access_token_cookie_key() == "access_key"

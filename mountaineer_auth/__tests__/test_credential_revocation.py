import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import asyncpg
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies
from jose import jwt

from mountaineer_auth import AuthDependencies, UnauthorizedError, change_password
from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.authorize import authorize_user
from mountaineer_auth.controllers.login_controller import (
    LoginController,
    LoginInvalid,
    LoginRequest,
)
from mountaineer_auth.controllers.signup_controller import (
    SignupController,
    SignupRequest,
)
from mountaineer_auth.controllers.verify_controller import (
    ResetPasswordInvalid,
    ResetPasswordRequest,
    VerifyController,
)
from mountaineer_auth.models import UserAuthMixin, VerificationType


@pytest_asyncio.fixture
async def auth_client(db_connection: DBConnection):
    app = FastAPI()
    app.dependency_overrides[DatabaseDependencies.get_db_connection] = lambda: (
        db_connection
    )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized(request: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=401, content={"detail": exc.detail})

    @app.get("/user-id")
    async def user_id(value: UUID = Depends(AuthDependencies.require_valid_user_id)):
        return str(value)

    @app.get("/user")
    async def user(value: UserAuthMixin = Depends(AuthDependencies.require_valid_user)):
        return str(value.id)

    @app.get("/admin")
    async def admin(
        value: UserAuthMixin = Depends(AuthDependencies.require_admin_user),
    ):
        return str(value.id)

    @app.get("/optional-id")
    async def optional_id(value: UUID | None = Depends(AuthDependencies.peek_user_id)):
        return str(value) if value is not None else None

    @app.get("/optional-user")
    async def optional_user(
        value: UserAuthMixin | None = Depends(AuthDependencies.peek_user),
    ):
        return str(value.id) if value is not None else None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize("reset", [False, True], ids=["password-change", "recovery"])
async def test_password_update_revokes_credentials(
    reset: bool,
    auth_client: AsyncClient,
    db_connection: DBConnection,
    config: models.AppConfig,
):
    # An attacker preregisters the owner's email and obtains a session and API JWT.
    signup = await SignupController().signup(
        signup_payload=SignupRequest(
            username="owner@example.com", password="old-password"
        ),
        auth_config=config,
        db_connection=db_connection,
    )
    user = (await db_connection.exec(select(models.User)))[0]
    assert isinstance(signup, JSONResponse)
    assert isinstance(user, models.User)
    assert not user.is_verified
    session_cookie = signup.headers["set-cookie"].split(";", 1)[0]
    api_token = authorize_user(user=user, auth_config=config)
    legacy_claims = jwt.get_unverified_claims(api_token)
    del legacy_claims["auth_version"]
    legacy_token = jwt.encode(
        legacy_claims, config.API_SECRET_KEY, algorithm=config.API_KEY_ALGORITHM
    )
    other_user = models.User(email="other@example.com", hashed_password="")
    await db_connection.insert([other_user])
    other_token = authorize_user(user=other_user, auth_config=config)

    reset_links = [
        models.VerificationState(
            code=str(uuid4()),
            user_id=user.id,
            verification_type=VerificationType.FORGOT_PASSWORD,
            expiration_date=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        for _ in range(2)
    ]
    await db_connection.insert(reset_links)
    old_cookies = [
        session_cookie,
        f'access_key="Bearer {api_token}"',
        f'access_key="Bearer {legacy_token}"',
    ]
    for cookie in old_cookies:
        for path in ("/user", "/user-id", "/optional-user", "/optional-id"):
            response = await auth_client.get(path, headers={"cookie": cookie})
            assert response.status_code == 200
            assert response.json() == str(user.id)

    if reset:
        await VerifyController().reset_password(
            verification_code=reset_links[0].code,
            payload=ResetPasswordRequest(
                password="new-password", verify_password="new-password"
            ),
            db_connection=db_connection,
            config=config,
        )
    else:
        assert user.verify_password("old-password")
        await change_password(
            user=user,
            password="new-password",
            auth_config=config,
            db_connection=db_connection,
        )

    # A login that verified the old password before recovery must not mint a
    # usable credential afterward, even if token issuance itself was delayed.
    delayed_token = authorize_user(user=user, auth_config=config)
    for cookie in [*old_cookies, f'access_key="Bearer {delayed_token}"']:
        for path in ("/user", "/user-id", "/admin"):
            assert (
                await auth_client.get(path, headers={"cookie": cookie})
            ).status_code == 401
        for path in ("/optional-user", "/optional-id"):
            response = await auth_client.get(path, headers={"cookie": cookie})
            assert response.status_code == 200
            assert response.json() is None

    unchanged = await auth_client.get(
        "/user-id", headers={"cookie": f'access_key="Bearer {other_token}"'}
    )
    assert unchanged.status_code == 200
    assert unchanged.json() == str(other_user.id)
    updated = (
        await db_connection.exec(select(models.User).where(models.User.id == user.id))
    )[0]
    assert updated.auth_version == 1
    assert updated.is_verified == reset
    assert updated.verify_password("new-password")
    assert all(
        link.is_used
        for link in await db_connection.exec(select(models.VerificationState))
    )

    # Stale authenticated requests cannot change the password again.
    with pytest.raises(UnauthorizedError):
        await change_password(
            user=user,
            password="attacker-password",
            auth_config=config,
            db_connection=db_connection,
        )
    for link in reset_links:
        with pytest.raises(ResetPasswordInvalid):
            await VerifyController().reset_password(
                verification_code=link.code,
                payload=ResetPasswordRequest(
                    password="attacker-password", verify_password="attacker-password"
                ),
                db_connection=db_connection,
                config=config,
            )
    with pytest.raises(LoginInvalid):
        await LoginController().login(
            login_payload=LoginRequest(username=user.email, password="old-password"),
            auth_config=config,
            db_connection=db_connection,
        )
    login = await LoginController().login(
        login_payload=LoginRequest(username=user.email, password="new-password"),
        auth_config=config,
        db_connection=db_connection,
    )
    assert isinstance(login, JSONResponse)
    response = await auth_client.get(
        "/user-id", headers={"cookie": login.headers["set-cookie"].split(";", 1)[0]}
    )
    assert response.status_code == 200
    assert response.json() == str(user.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims",
    [
        {"auth_version": None},
        {"auth_version": False},
        {"auth_version": "0"},
        {"auth_version": 0.0},
        {"auth_version": -1},
        {"auth_version": 1},
        {"auth_version": 0, "user_id": "invalid"},
        {"auth_version": 0, "user_id": None},
        {"auth_version": 0, "exp": 0},
    ],
)
async def test_invalid_credentials_fail_all_authentication_paths(
    claims: dict,
    auth_client: AsyncClient,
    db_connection: DBConnection,
    config: models.AppConfig,
):
    user = models.User(email="admin@example.com", hashed_password="", is_admin=True)
    await db_connection.insert([user])
    token = jwt.encode(
        {
            "user_id": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            **claims,
        },
        config.API_SECRET_KEY,
        algorithm=config.API_KEY_ALGORITHM,
    )
    for path in ("/user", "/user-id", "/admin"):
        response = await auth_client.get(
            path, headers={"cookie": f'access_key="Bearer {token}"'}
        )
        assert response.status_code == 401
    for path in ("/optional-user", "/optional-id"):
        response = await auth_client.get(
            path, headers={"cookie": f'access_key="Bearer {token}"'}
        )
        assert response.status_code == 200
        assert response.json() is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid", ["expired", "used", "initial", "mismatch", "missing", "orphan"]
)
async def test_invalid_reset_does_not_change_account(
    invalid: str, db_connection: DBConnection, config: models.AppConfig
):
    user = models.User(
        email="owner@example.com",
        hashed_password=models.User.get_password_hash("old-password"),
    )
    await db_connection.insert([user])
    link = models.VerificationState(
        code=str(uuid4()),
        user_id=uuid4() if invalid == "orphan" else user.id,
        verification_type=VerificationType.INITIAL
        if invalid == "initial"
        else VerificationType.FORGOT_PASSWORD,
        expiration_date=datetime.now(timezone.utc)
        + timedelta(minutes=-1 if invalid == "expired" else 15),
        is_used=invalid == "used",
    )
    if invalid != "missing":
        await db_connection.insert([link])

    with pytest.raises(ResetPasswordInvalid):
        await VerifyController().reset_password(
            verification_code=link.code,
            payload=ResetPasswordRequest(
                password="new-password",
                verify_password="different"
                if invalid == "mismatch"
                else "new-password",
            ),
            db_connection=db_connection,
            config=config,
        )
    unchanged = (await db_connection.exec(select(models.User)))[0]
    assert unchanged.hashed_password == user.hashed_password
    assert unchanged.auth_version == 0
    assert not unchanged.is_verified
    links = await db_connection.exec(select(models.VerificationState))
    assert not links or links[0].is_used == link.is_used


@pytest.mark.asyncio
async def test_failed_recovery_rolls_back_password_version_and_reset_links(
    db_connection: DBConnection, config: models.AppConfig
):
    user = models.User(email="owner@example.com", hashed_password="original-hash")
    link = models.VerificationState(
        code=str(uuid4()),
        user_id=user.id,
        verification_type=VerificationType.FORGOT_PASSWORD,
        expiration_date=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    await db_connection.insert([user, link])
    # Force the final email-verification write to fail after the password and
    # reset links were updated, exercising a real database rollback.
    await db_connection.conn.execute(
        'ALTER TABLE "user" ADD CONSTRAINT reject_verification CHECK (NOT is_verified)'
    )
    with pytest.raises(asyncpg.CheckViolationError):
        await VerifyController().reset_password(
            verification_code=link.code,
            payload=ResetPasswordRequest(
                password="new-password", verify_password="new-password"
            ),
            db_connection=db_connection,
            config=config,
        )
    unchanged = (await db_connection.exec(select(models.User)))[0]
    assert unchanged.hashed_password == user.hashed_password
    assert unchanged.auth_version == 0
    assert not unchanged.is_verified
    assert not (await db_connection.exec(select(models.VerificationState)))[0].is_used


@pytest.mark.asyncio
@pytest.mark.parametrize("same_link", [True, False])
async def test_concurrent_recovery_succeeds_only_once(
    same_link: bool, db_connection: DBConnection, config: models.AppConfig
):
    user = models.User(email="owner@example.com", hashed_password="")
    await db_connection.insert([user])
    links = [
        models.VerificationState(
            code=str(uuid4()),
            user_id=user.id,
            verification_type=VerificationType.FORGOT_PASSWORD,
            expiration_date=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        for _ in range(2)
    ]
    await db_connection.insert(links)
    connections = [
        DBConnection(await asyncpg.connect(db_connection.get_dsn())) for _ in range(2)
    ]
    tasks = []
    try:
        # Hold the account lock until both independent requests are blocked on it.
        async with db_connection.transaction():
            await db_connection.exec(
                select(models.User).where(models.User.id == user.id).for_update()
            )
            for index, connection in enumerate(connections):
                tasks.append(
                    asyncio.ensure_future(
                        VerifyController().reset_password(
                            verification_code=links[0 if same_link else index].code,
                            payload=ResetPasswordRequest(
                                password=f"password-{index}",
                                verify_password=f"password-{index}",
                            ),
                            db_connection=connection,
                            config=config,
                        )
                    )
                )
            async with asyncio.timeout(5):
                while True:
                    waiting = await db_connection.conn.fetchval(
                        "SELECT count(*) FROM unnest($1::int[]) AS pid WHERE cardinality(pg_blocking_pids(pid)) > 0",
                        [
                            connection.conn.get_server_pid()
                            for connection in connections
                        ],
                    )
                    if waiting == 2:
                        break
                    await asyncio.sleep(0.01)
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True), timeout=5
        )
        successes = [
            index
            for index, result in enumerate(results)
            if not isinstance(result, BaseException)
        ]
        assert len(successes) == 1, results
        assert sum(isinstance(result, ResetPasswordInvalid) for result in results) == 1
        updated = (await db_connection.exec(select(models.User)))[0]
        assert isinstance(updated, models.User)
        assert updated.auth_version == 1
        winner = successes[0]
        assert updated.verify_password(f"password-{winner}")
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for connection in connections:
            await connection.close()

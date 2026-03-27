import pytest

from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.controllers.signup_controller import SignupController


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, expected_username",
    [
        ("myemail@example.com", "myemail@example.com"),
        ("MyEmail@example.com", "myemail@example.com"),
        ("myemail@example.com  ", "myemail@example.com"),
    ],
)
async def test_build_user_normalize_username(email: str, expected_username: str):
    signup_controller = SignupController(post_signup_redirect="/")
    user = await signup_controller.build_user(
        model=models.User,
        username=email,
        hashed_password="",
    )

    assert user.email == expected_username

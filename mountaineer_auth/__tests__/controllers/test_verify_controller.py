from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import pytest
from iceaxe import DBConnection

from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.controllers.verify_controller import VerifyController
from mountaineer_auth.models import VerificationState, VerificationType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "verification_state,expected_not_found,expected_expired,expected_is_used,expected_success",
    [
        # Test case 1: Verification state is None
        (None, True, False, False, False),
        # Test case 2: Verification is expired
        (
            VerificationState(
                code="test-code",
                user_id=uuid4(),
                verification_type=VerificationType.INITIAL,
                expiration_date=datetime.now(timezone.utc) - timedelta(days=1),
                is_used=False,
            ),
            False,
            True,
            False,
            False,
        ),
        # Test case 3: Verification is already used
        (
            VerificationState(
                code="test-code",
                user_id=uuid4(),
                verification_type=VerificationType.INITIAL,
                expiration_date=datetime.now(timezone.utc) + timedelta(days=1),
                is_used=True,
            ),
            False,
            False,
            True,
            False,
        ),
    ],
)
async def test_verify_controller_render(
    verification_state: Optional[VerificationState],
    expected_not_found: bool,
    expected_expired: bool,
    expected_is_used: bool,
    expected_success: bool,
    db_connection: DBConnection,
    config: models.AppConfig,
) -> None:
    """
    Test the VerifyController's render function with different verification states.
    """
    controller = VerifyController()

    # If we have a verification state, insert it into the database
    if verification_state is not None:
        await db_connection.insert([verification_state])

    result = await controller.render(
        verification_code="test-code",
        db_connection=db_connection,
        config=config,
    )

    assert result.not_found == expected_not_found
    assert result.expired == expected_expired
    assert result.is_used == expected_is_used
    assert result.success == expected_success
    assert result.verification_code == "test-code"

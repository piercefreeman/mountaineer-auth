from math import isclose
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.cloud.recaptchaenterprise_v1.services.recaptcha_enterprise_service.async_client import (
    RecaptchaEnterpriseServiceAsyncClient,
)
from google.cloud.recaptchaenterprise_v1.types import (
    Assessment,
    Event,
    RiskAnalysis,
    TokenProperties,
)

from mountaineer_auth import dependencies as AuthDependencies
from mountaineer_auth.config import AuthConfig
from mountaineer_auth.recaptcha import RecaptchaValidationError, validate_recaptcha


@pytest.fixture
def mock_recaptcha_client() -> RecaptchaEnterpriseServiceAsyncClient:
    client = MagicMock(spec=RecaptchaEnterpriseServiceAsyncClient)
    client.create_assessment = AsyncMock()
    client.common_project_path = MagicMock(return_value="projects/your_project")
    return client


@pytest.fixture
def mock_dependencies(
    monkeypatch: Any,
    mock_recaptcha_client: RecaptchaEnterpriseServiceAsyncClient,
    config: AuthConfig,
) -> None:
    async def mock_get_recaptcha_client() -> RecaptchaEnterpriseServiceAsyncClient:
        return mock_recaptcha_client

    monkeypatch.setattr(
        AuthDependencies, "get_recaptcha_client", mock_get_recaptcha_client
    )


@pytest.mark.asyncio
async def test_validate_recaptcha_success(
    mock_dependencies: None,
    mock_recaptcha_client: MagicMock,
    config: AuthConfig,
) -> None:
    recaptcha_token: str = "valid_token"
    action_name: str = "login"
    expected_score: float = 0.9
    # https://github.com/googleapis/googleapis/blob/master/google/cloud/recaptchaenterprise/v1/recaptchaenterprise.proto
    expected_reasons = [
        RiskAnalysis.ClassificationReason.CLASSIFICATION_REASON_UNSPECIFIED
    ]

    assessment: Assessment = Assessment(
        name="assessment_name",
        event=Event(token=recaptcha_token),
        risk_analysis=RiskAnalysis(score=expected_score, reasons=expected_reasons),
        token_properties=TokenProperties(valid=True, action=action_name),
    )
    mock_recaptcha_client.create_assessment.return_value = assessment

    result = await validate_recaptcha(recaptcha_token, action_name)
    # Protobuf floating point inprecision can cause issues with direct comparison
    assert isclose(result.score, expected_score, rel_tol=1e-5)
    assert result.risk_reasons == ["CLASSIFICATION_REASON_UNSPECIFIED"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token_valid, action_valid, risk_analysis_present, expected_exception",
    [
        (False, True, True, RecaptchaValidationError),
        (True, False, True, RecaptchaValidationError),
        (True, True, False, RecaptchaValidationError),
    ],
)
async def test_validate_recaptcha_failures(
    mock_dependencies: None,
    mock_recaptcha_client: MagicMock,
    token_valid: bool,
    action_valid: bool,
    risk_analysis_present: bool,
    expected_exception: type[BaseException],
) -> None:
    recaptcha_token: str = "test_token"
    action_name: str = "login"
    wrong_action_name: str = "register"

    assessment = Assessment(
        name="assessment_name",
        event=Event(token=recaptcha_token),
        risk_analysis=RiskAnalysis(score=0.5, reasons=[])
        if risk_analysis_present
        else None,
        token_properties=TokenProperties(
            valid=token_valid, action=action_name if action_valid else wrong_action_name
        ),
    )
    mock_recaptcha_client.create_assessment.return_value = assessment

    with pytest.raises(expected_exception):
        await validate_recaptcha(recaptcha_token, action_name)

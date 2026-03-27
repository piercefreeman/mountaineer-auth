from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import Depends

if TYPE_CHECKING:
    from google.cloud.recaptchaenterprise_v1 import (
        RecaptchaEnterpriseServiceAsyncClient,
    )
else:
    RecaptchaEnterpriseServiceAsyncClient = None

try:
    from google.cloud.recaptchaenterprise_v1 import (
        RecaptchaEnterpriseServiceAsyncClient,
    )

    RECAPTCHA_IS_AVAILABLE = True
except ImportError:
    RECAPTCHA_IS_AVAILABLE = False

from mountaineer import CoreDependencies
from mountaineer.dependencies import get_function_dependencies

from mountaineer_auth import dependencies as AuthDependencies
from mountaineer_auth.config import AuthConfig


@dataclass
class RiskResult:
    score: float
    risk_reasons: list[Any]


class RecaptchaValidationError(Exception):
    pass


async def validate_recaptcha(
    recaptcha_token: str,
    action_name: str,
):
    """
    Validate a reCAPTCHA token generated from the client javascript
    and return the score and reasons for the score.

    """
    if not RECAPTCHA_IS_AVAILABLE:
        raise ImportError(
            "The reCAPTCHA library is not available. Please install the google-cloud-recaptchaenterprise library."
        )

    async def validate_recaptcha_async(
        recaptcha_client: RecaptchaEnterpriseServiceAsyncClient = Depends(
            AuthDependencies.get_recaptcha_client
        ),
        config: AuthConfig = Depends(CoreDependencies.get_config_with_type(AuthConfig)),
    ):
        if not config.RECAPTCHA:
            raise ValueError("The reCAPTCHA config is not set in the config")

        project_path = recaptcha_client.common_project_path(
            config.RECAPTCHA.gcp_project_id
        )

        captchaRequest = {
            "assessment": {
                "event": {
                    "token": recaptcha_token,
                    "site_key": config.RECAPTCHA.gcp_client_key,
                }
            },
            "parent": project_path,
        }

        # client.create_assessment() can return a Promise or take a Callback
        assessment = await recaptcha_client.create_assessment(captchaRequest)

        # Check if the token is valid
        if not assessment.token_properties:
            raise RecaptchaValidationError(
                "The CreateAssessment call failed because the token was invalid"
            )
        if not assessment.token_properties.valid:
            raise RecaptchaValidationError(
                f"The CreateAssessment call failed because the token was: {assessment.token_properties}\n",
                "If you get the error 'BROWSER_ERROR' this likely means your domain hasn't been allowed: https://console.cloud.google.com/security/recaptcha.",
            )

        if not assessment.risk_analysis:
            raise RecaptchaValidationError(
                "The CreateAssessment call failed because the token was invalid"
            )

        # Check if the expected action was executed
        if assessment.token_properties.action != action_name:
            raise RecaptchaValidationError(
                "The action attribute in your reCAPTCHA tag does not match the action you are expecting to score"
            )

        return RiskResult(
            score=assessment.risk_analysis.score,
            risk_reasons=([reason.name for reason in assessment.risk_analysis.reasons]),
        )

    async with get_function_dependencies(callable=validate_recaptcha_async) as values:
        return await validate_recaptcha_async(**values)

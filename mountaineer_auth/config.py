from typing import Type

from pydantic import model_validator
from pydantic_settings import BaseSettings

from mountaineer_auth.models import UserAuthMixin, VerificationState

#
# All nested setting models need to have lowercase attribute names
# https://github.com/pydantic/pydantic-settings/issues/43
#


class AuthRecaptchaConfig(BaseSettings):
    # base64 encoded service-account access key
    gcp_service: str
    # Project ID that hosts your ReCapcha, includes the GCP service account definition
    gcp_project_id: str
    # Client-side key for browser embedding, tied to your GCP ReCapcha instance
    gcp_client_key: str


class AuthEmailConfig(BaseSettings):
    header_image: str | None = None
    unsubscribe_url: str

    # Used for absolute links
    server_host: str

    # Specify company name and address - this is required
    # for email compliance
    project_name: str
    project_address: str


class AuthConfig(BaseSettings):
    """
    Auth configuration plugin.

    We expect your application configuration
    to specify a [env_nested_delimiter](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
    to be able to override these nested configurations.

    """

    API_SECRET_KEY: str
    API_KEY_ALGORITHM: str = "HS256"

    RECAPTCHA_ENABLED: bool = False
    RECAPTCHA: AuthRecaptchaConfig | None = None

    AUTH_EMAIL_ENABLED: bool = False
    AUTH_EMAIL: AuthEmailConfig | None = None

    AUTH_USER: Type[UserAuthMixin]
    AUTH_VERIFICATION_STATE: Type[VerificationState]

    @model_validator(mode="after")
    def validate_recaptcha(self: "AuthConfig") -> "AuthConfig":
        if self.RECAPTCHA_ENABLED and not self.RECAPTCHA:
            raise ValueError(
                'RECAPTCHA__XX configurations is required.\n Make sure to specify `env_nested_delimiter="__" in your AppConfig.'
            )

        return self

    @model_validator(mode="after")
    def validate_email(self: "AuthConfig") -> "AuthConfig":
        if self.AUTH_EMAIL_ENABLED and not self.AUTH_EMAIL:
            raise ValueError("EMAIL__X is required")

        return self

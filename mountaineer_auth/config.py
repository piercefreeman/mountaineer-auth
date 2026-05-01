from typing import Type

from pydantic import EmailStr, model_validator
from pydantic_settings import BaseSettings

from mountaineer_auth.models import UserAuthMixin, VerificationState

#
# All nested setting models need to have lowercase attribute names
# https://github.com/pydantic/pydantic-settings/issues/43
#


class AuthEmailConfig(BaseSettings):
    header_image: str | None = None

    from_email: EmailStr
    from_name: str | None = None

    # Used for absolute links
    server_host: str

    # Specify company name and address - this is required
    # for email compliance
    project_name: str
    project_address: str
    unsubscribe_url: str


class AuthConfig(BaseSettings):
    """
    Auth configuration plugin.

    We expect your application configuration
    to specify a [env_nested_delimiter](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
    to be able to override these nested configurations.

    """

    API_SECRET_KEY: str
    API_KEY_ALGORITHM: str = "HS256"
    AUTH_LOGIN_EXPIRATION_MINUTES: int = 60 * 24

    AUTH_EMAIL_ENABLED: bool = False
    AUTH_EMAIL: AuthEmailConfig | None = None

    AUTH_USER: Type[UserAuthMixin]
    AUTH_VERIFICATION_STATE: Type[VerificationState]

    @model_validator(mode="after")
    def validate_email(self: "AuthConfig") -> "AuthConfig":
        if self.AUTH_EMAIL_ENABLED and not self.AUTH_EMAIL:
            raise ValueError("EMAIL__X is required")

        return self

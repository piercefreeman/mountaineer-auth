from iceaxe.mountaineer import DatabaseConfig
from mountaineer_cloud.providers.resend import ResendConfig
from pydantic_settings import SettingsConfigDict

from mountaineer import ConfigBase

from example_app import models
from mountaineer_auth import AuthConfig, AuthEmailConfig


class AppConfig(AuthConfig, DatabaseConfig, ResendConfig, ConfigBase):
    PACKAGE: str | None = "example_app"
    API_SECRET_KEY: str = "development-secret-key"
    RESEND_API_KEY: str = "re_example_dummy_key"

    AUTH_EMAIL_ENABLED: bool = False
    AUTH_EMAIL: AuthEmailConfig | None = AuthEmailConfig(
        unsubscribe_url="http://localhost:3000/unsubscribe",
        from_email="onboarding@resend.dev", # should be whitelisted for all accounts
        from_name="Example App",
        server_host="http://localhost:3000",
        project_name="Example App",
        project_address="123 Example Street, San Francisco, CA 94107",
    )

    AUTH_USER: type[models.User] = models.User
    AUTH_VERIFICATION_STATE: type[models.VerificationState] = (
        models.VerificationState
    )

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_nested_delimiter="__",
    )

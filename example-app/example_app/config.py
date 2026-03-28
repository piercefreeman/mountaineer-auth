from iceaxe.mountaineer import DatabaseConfig
from pydantic_settings import SettingsConfigDict

from mountaineer import ConfigBase

from example_app import models
from mountaineer_auth import AuthConfig


class AppConfig(AuthConfig, DatabaseConfig, ConfigBase):
    PACKAGE: str | None = "example_app"
    API_SECRET_KEY: str = "development-secret-key"
    AUTH_USER: type[models.User] = models.User
    AUTH_VERIFICATION_STATE: type[models.VerificationState] = (
        models.VerificationState
    )

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_nested_delimiter="__",
    )

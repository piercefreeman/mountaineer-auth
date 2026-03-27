from iceaxe import TableBase
from iceaxe.mountaineer import DatabaseConfig

from mountaineer import ConfigBase

from mountaineer_auth.config import AuthConfig
from mountaineer_auth.models import (
    UserAuthMixin,
    VerificationState as VerificationStateBase,
)


class AppConfig(AuthConfig, DatabaseConfig, ConfigBase):
    pass


class User(UserAuthMixin, TableBase):
    pass


class VerificationState(VerificationStateBase, TableBase):
    pass

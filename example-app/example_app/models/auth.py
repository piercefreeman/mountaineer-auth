from iceaxe import TableBase

from mountaineer_auth.models import (
    UserAuthMixin,
    VerificationState as VerificationStateBase,
)


class User(UserAuthMixin, TableBase):
    pass


class VerificationState(VerificationStateBase, TableBase):
    pass

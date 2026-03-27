from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

import bcrypt
from iceaxe import Field, PostgresDateTime, TableBase


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password=plain_password.encode(), hashed_password=hashed_password.encode()
    )


class UserAuthMixin(TableBase, autodetect=False):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True)
    hashed_password: str
    is_verified: bool = False
    is_admin: bool = False

    def verify_password(self, plain_password: str) -> bool:
        return verify_password(plain_password, self.hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return hash_password(password)


class VerificationType(StrEnum):
    INITIAL = "INITIAL"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"


class VerificationState(TableBase):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str
    user_id: UUID

    verification_type: VerificationType

    expiration_date: datetime = Field(
        default_factory=datetime.now,
        postgres_config=PostgresDateTime(timezone=True),
    )

    is_used: bool = False

from uuid import UUID

from fastapi import Depends
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies
from mountaineer_auth import EmailControllerBase, EmailMetadata, EmailRenderBase
from pydantic import BaseModel

from mountaineer import CoreDependencies, LinkAttribute, ManagedViewPath, Metadata

from mountaineer_auth.config import AuthConfig
from mountaineer_auth.emails.common import CommonEmailConfig
from mountaineer_auth.views import get_auth_view_path


class VerifyEmailRequest(BaseModel):
    verification_host: str
    verification_code: str
    user_name: str | None = None
    user_id: UUID


class VerifyEmailRender(EmailRenderBase):
    verification_host: str
    verification_code: str
    user_name: str | None
    common_config: CommonEmailConfig


class VerifyEmailController(EmailControllerBase[VerifyEmailRequest]):
    view_path = (
        ManagedViewPath.from_view_root(get_auth_view_path(""), package_root_link=None)
        / "emails/verify_email/page.tsx"
    )

    async def render(
        self,
        payload: VerifyEmailRequest,
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
        config: AuthConfig = Depends(CoreDependencies.get_config_with_type(AuthConfig)),
    ) -> VerifyEmailRender:
        users = await db_connection.exec(
            select(config.AUTH_USER).where(config.AUTH_USER.id == payload.user_id)
        )
        user = users[0] if users else None
        if not user:
            raise ValueError(f"User not found: {payload.user_id}")

        # Require email mode to be enabled
        if not config.AUTH_EMAIL_ENABLED or config.AUTH_EMAIL is None:
            raise ValueError("Email mode is not enabled")

        return VerifyEmailRender(
            user_name=payload.user_name,
            verification_host=payload.verification_host,
            verification_code=payload.verification_code,
            common_config=CommonEmailConfig(
                header_image=config.AUTH_EMAIL.header_image,
                unsubscribe_url=config.AUTH_EMAIL.unsubscribe_url,
                project_name=config.AUTH_EMAIL.project_name,
                project_address=config.AUTH_EMAIL.project_address,
            ),
            email_metadata=EmailMetadata(
                subject="Verify your email",
                to_email=user.email,
            ),
            metadata=Metadata(
                links=[
                    LinkAttribute(
                        rel="stylesheet", href=f"{self._scripts_prefix}/auth_main.css"
                    )
                ]
            ),
        )

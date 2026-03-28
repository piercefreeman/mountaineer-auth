from mountaineer_email import EmailControllerBase, EmailMetadata, EmailRenderBase
from pydantic import BaseModel

from mountaineer import LinkAttribute, Metadata


class WelcomePreviewEmailRequest(BaseModel):
    recipient_name: str


class WelcomePreviewEmailRender(EmailRenderBase):
    recipient_name: str


class WelcomePreviewEmail(EmailControllerBase[WelcomePreviewEmailRequest]):
    view_path = "/emails/welcome_preview/page.tsx"

    async def render(
        self,
        payload: WelcomePreviewEmailRequest,
    ) -> WelcomePreviewEmailRender:
        return WelcomePreviewEmailRender(
            recipient_name=payload.recipient_name,
            email_metadata=EmailMetadata(
                subject=f"Welcome aboard, {payload.recipient_name}",
            ),
            metadata=Metadata(
                links=[
                    LinkAttribute(rel="stylesheet", href="/static/emails_main.css"),
                ],
            ),
        )

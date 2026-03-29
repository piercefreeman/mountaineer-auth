from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Any, TypeVar, cast

from mountaineer_cloud.primitives import EmailBody, EmailMessage, EmailRecipient
from mountaineer_cloud.providers.definition import resolve_cloud_by_config
from mountaineer_cloud.providers_common.email import EmailProviderCore
from mountaineer_email.controller import EmailControllerBase
from mountaineer_email.registry import controller_to_registry_id, get_email_controller
from mountaineer_email.render import FilledOutEmail
from pydantic import BaseModel, EmailStr
from waymark import Depend, RetryPolicy, Workflow, action, workflow

from mountaineer.config import get_config

from mountaineer_auth.emails.forgot_password_email import ForgotPasswordEmailController
from mountaineer_auth.emails.verify_email import VerifyEmailController

RenderInput = TypeVar("RenderInput", bound=BaseModel)

AUTH_EMAIL_WORKFLOW_CONTROLLERS: dict[str, type[EmailControllerBase[Any]]] = {
    VerifyEmailController.workflow_label: VerifyEmailController,
    ForgotPasswordEmailController.workflow_label: ForgotPasswordEmailController,
}


def _controller_to_email_key(
    controller: type[EmailControllerBase[Any]],
) -> str:
    try:
        workflow_label = controller.workflow_label
    except AttributeError as exc:
        raise ValueError(
            f"{controller.__name__} must define a workflow_label to be used in auth email workflows."
        ) from exc

    if AUTH_EMAIL_WORKFLOW_CONTROLLERS.get(workflow_label) is not controller:
        raise ValueError(
            f"{controller.__name__} is not a supported auth email workflow controller."
        )

    return workflow_label


def _email_key_to_registry_id(email_key: str) -> str:
    controller = AUTH_EMAIL_WORKFLOW_CONTROLLERS.get(email_key)
    if controller is None:
        raise ValueError(f"Unsupported auth email workflow key '{email_key}'.")
    return controller_to_registry_id(controller)


class SendAuthEmailInput(BaseModel):
    email_key: str
    email_input: dict[str, Any]
    to_email: EmailStr
    to_name: str | None = None
    from_email: EmailStr
    from_name: str | None = None

    @classmethod
    def from_email_input(
        cls,
        controller: type[EmailControllerBase[RenderInput]],
        *,
        email_input: RenderInput,
        to_email: str,
        to_name: str | None = None,
        from_email: str,
        from_name: str | None = None,
    ) -> "SendAuthEmailInput":
        return cls(
            email_key=_controller_to_email_key(controller),
            email_input=email_input.model_dump(mode="json"),
            to_email=to_email,
            to_name=to_name,
            from_email=from_email,
            from_name=from_name,
        )


class ConstructedAuthEmail(BaseModel):
    to_email: EmailStr
    to_name: str | None = None
    from_email: EmailStr
    from_name: str | None = None
    subject: str
    html_body: str


class SendAuthEmailResult(BaseModel):
    message_id: str


async def get_auth_email_core() -> AsyncGenerator[EmailProviderCore[Any], None]:
    config = get_config()
    matching_providers = resolve_cloud_by_config(config, EmailProviderCore)

    if len(matching_providers) > 1:
        raise TypeError(
            "Config matches multiple email providers. "
            "Auth email workflows require exactly one configured email provider."
        )
    if not matching_providers:
        raise TypeError(
            "Config must expose exactly one mountaineer-cloud email provider."
        )

    provider = matching_providers[0]
    async for core in provider.injection_function():
        yield cast(EmailProviderCore[Any], core)
    return


@action
async def construct_auth_email(
    payload: SendAuthEmailInput,
) -> ConstructedAuthEmail:
    registry_id = _email_key_to_registry_id(payload.email_key)
    try:
        email_controller = get_email_controller(registry_id)
    except KeyError as exc:
        raise ValueError(
            f"Email controller is not registered for auth email key '{payload.email_key}'."
        ) from exc

    rendered_email = cast(
        FilledOutEmail,
        await email_controller.render_obj(payload.email_input),
    )

    return ConstructedAuthEmail(
        to_email=payload.to_email,
        to_name=payload.to_name,
        from_email=payload.from_email,
        from_name=payload.from_name,
        subject=rendered_email.subject,
        html_body=rendered_email.html_body,
    )


@action
async def send_constructed_auth_email(
    payload: ConstructedAuthEmail,
    core: EmailProviderCore[Any] = Depend(get_auth_email_core),  # type: ignore[assignment]
) -> SendAuthEmailResult:
    message = EmailMessage[Any](
        sender=EmailRecipient(
            email=str(payload.from_email),
            display_name=payload.from_name,
        ),
        recipient=EmailRecipient(
            email=str(payload.to_email),
            display_name=payload.to_name,
        ),
        subject=payload.subject,
        body=EmailBody(html=payload.html_body),
    )
    message_id = await message.send(core)
    return SendAuthEmailResult(message_id=message_id)


@workflow
class SendAuthEmail(Workflow):
    async def run(
        self,
        email_key: str,
        email_input: dict[str, Any],
        to_email: str,
        from_email: str,
        to_name: str | None = None,
        from_name: str | None = None,
    ) -> SendAuthEmailResult:
        payload = SendAuthEmailInput(
            email_key=email_key,
            email_input=email_input,
            to_email=to_email,
            to_name=to_name,
            from_email=from_email,
            from_name=from_name,
        )

        constructed_email = await self.run_action(
            construct_auth_email(payload),
            retry=RetryPolicy(attempts=2, backoff_seconds=1),
            timeout=timedelta(seconds=60),
        )

        return await self.run_action(
            send_constructed_auth_email(constructed_email),
            retry=RetryPolicy(attempts=3, backoff_seconds=5),
            timeout=timedelta(seconds=60),
        )

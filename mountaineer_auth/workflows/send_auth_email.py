from collections.abc import AsyncGenerator
from datetime import timedelta
from inspect import isclass
from typing import Any, TypeVar, cast

from pydantic import BaseModel, EmailStr, field_validator
from waymark import Depend, RetryPolicy, Workflow, action, workflow

from mountaineer.config import get_config
from mountaineer.dependencies import get_function_dependencies

from mountaineer_cloud.primitives import EmailBody, EmailMessage, EmailRecipient
from mountaineer_cloud.providers.definition import resolve_cloud_by_config
from mountaineer_cloud.providers_common.email import EmailProviderCore
from mountaineer_email.controller import EmailControllerBase
from mountaineer_email.registry import (
    SerializedEmailController,
    deserialize_controller,
    serialize_controller,
)

RenderInput = TypeVar("RenderInput", bound=BaseModel)


class SendAuthEmailInput(BaseModel):
    email_controller: SerializedEmailController
    email_input: dict[str, Any]
    to_email: EmailStr
    to_name: str | None = None
    from_email: EmailStr
    from_name: str | None = None

    @field_validator("email_controller", mode="before")
    @classmethod
    def serialize_email_controller_reference(cls, value: Any) -> Any:
        if (isclass(value) and issubclass(value, EmailControllerBase)) or isinstance(
            value, EmailControllerBase
        ):
            return serialize_controller(value)

        return value

    @classmethod
    def from_email_input(
        cls,
        controller: type[EmailControllerBase[RenderInput]]
        | EmailControllerBase[RenderInput],
        *,
        email_input: RenderInput,
        to_email: str,
        to_name: str | None = None,
        from_email: str,
        from_name: str | None = None,
    ) -> "SendAuthEmailInput":
        return cls.model_validate(
            {
                "email_controller": controller,
                "email_input": email_input.model_dump(mode="json"),
                "to_email": to_email,
                "to_name": to_name,
                "from_email": from_email,
                "from_name": from_name,
            }
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
    async with get_function_dependencies(callable=provider.injection_function) as deps:
        async for core in provider.injection_function(**deps):
            yield cast(EmailProviderCore[Any], core)
    return


@action
async def construct_auth_email(
    email_controller: SerializedEmailController,
    email_input: dict[str, Any],
    to_email: str,
    from_email: str,
    to_name: str | None = None,
    from_name: str | None = None,
) -> ConstructedAuthEmail:
    payload = SendAuthEmailInput(
        email_controller=email_controller,
        email_input=email_input,
        to_email=to_email,
        to_name=to_name,
        from_email=from_email,
        from_name=from_name,
    )
    controller_instance = deserialize_controller(payload.email_controller)
    rendered_email = await controller_instance.render_obj(payload.email_input)

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
        email_controller: SerializedEmailController,
        email_input: dict[str, Any],
        to_email: str,
        from_email: str,
        to_name: str | None = None,
        from_name: str | None = None,
    ) -> SendAuthEmailResult:
        constructed_email = await self.run_action(
            construct_auth_email(
                email_controller=email_controller,
                email_input=email_input,
                to_email=to_email,
                to_name=to_name,
                from_email=from_email,
                from_name=from_name,
            ),
            retry=RetryPolicy(attempts=2, backoff_seconds=1),
            timeout=timedelta(seconds=60),
        )

        return await self.run_action(
            send_constructed_auth_email(constructed_email),
            retry=RetryPolicy(attempts=3, backoff_seconds=5),
            timeout=timedelta(seconds=60),
        )

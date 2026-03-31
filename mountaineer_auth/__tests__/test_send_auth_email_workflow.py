from dataclasses import dataclass, field
from typing import Any
from unittest.mock import patch

import pytest
from mountaineer_cloud.providers.definition import ProviderDefinition
from mountaineer_cloud.providers.resend import ResendConfig
from mountaineer_cloud.providers_common.email import (
    EmailBody,
    EmailProviderCore,
    EmailRecipient,
)
from mountaineer_email import EmailControllerBase, EmailMetadata, EmailRenderBase
from mountaineer_email.render import FilledOutEmail
from pydantic import BaseModel

from mountaineer import CoreDependencies, Depends
from mountaineer.config import ConfigBase, register_config_in_context

from mountaineer_auth.workflows.send_auth_email import (
    AUTH_EMAIL_WORKFLOW_CONTROLLERS,
    ConstructedAuthEmail,
    SendAuthEmail,
    SendAuthEmailInput,
    construct_auth_email,
    send_constructed_auth_email,
)


class MockWorkflowEmailRequest(BaseModel):
    recipient_name: str


class MockWorkflowEmailRender(EmailRenderBase):
    recipient_name: str


class MockWorkflowEmailController(EmailControllerBase[MockWorkflowEmailRequest]):
    workflow_label = "mock_email"

    async def render(
        self,
        payload: MockWorkflowEmailRequest,
    ) -> MockWorkflowEmailRender:
        return MockWorkflowEmailRender(
            recipient_name=payload.recipient_name,
            email_metadata=EmailMetadata(
                subject=f"Hello {payload.recipient_name}",
            ),
        )

    async def render_obj(
        self,
        render_obj: BaseModel | dict[str, Any],
        *,
        request=None,
    ) -> FilledOutEmail:
        payload = (
            render_obj
            if isinstance(render_obj, MockWorkflowEmailRequest)
            else MockWorkflowEmailRequest.model_validate(render_obj)
        )
        return FilledOutEmail(
            subject=f"Hello {payload.recipient_name}",
            html_body=f"<p>Hello {payload.recipient_name}</p>",
        )


class WorkflowTestConfig(ResendConfig, ConfigBase):
    pass


@dataclass
class FakeEmailCore(EmailProviderCore[Any]):
    config: Any = None
    session: Any = None
    messages: list[dict[str, Any]] = field(default_factory=list)

    async def email_send(
        self,
        *,
        sender: EmailRecipient,
        recipient: EmailRecipient,
        subject: str,
        body: EmailBody,
    ) -> str:
        self.messages.append(
            {
                "sender": sender,
                "recipient": recipient,
                "subject": subject,
                "body": body,
            }
        )
        return "provider-message-id"


@pytest.fixture
def registered_mock_email_controller():
    with patch.dict(
        AUTH_EMAIL_WORKFLOW_CONTROLLERS,
        {"mock_email": MockWorkflowEmailController},
        clear=True,
    ):
        yield MockWorkflowEmailController()


@pytest.mark.asyncio
async def test_construct_auth_email_action(
    registered_mock_email_controller: MockWorkflowEmailController,
):
    del registered_mock_email_controller

    payload = SendAuthEmailInput.from_email_input(
        MockWorkflowEmailController,
        email_input=MockWorkflowEmailRequest(recipient_name="Ada"),
        to_email="ada@example.com",
        to_name="Ada Lovelace",
        from_email="noreply@example.com",
        from_name="Example App",
    )

    result = await construct_auth_email(payload)

    assert result.to_email == "ada@example.com"
    assert result.to_name == "Ada Lovelace"
    assert result.from_email == "noreply@example.com"
    assert result.from_name == "Example App"
    assert result.subject == "Hello Ada"
    assert result.html_body == "<p>Hello Ada</p>"


@pytest.mark.asyncio
async def test_send_constructed_auth_email_action():
    core = FakeEmailCore()

    result = await send_constructed_auth_email(
        ConstructedAuthEmail(
            to_email="ada@example.com",
            to_name="Ada Lovelace",
            from_email="noreply@example.com",
            from_name="Example App",
            subject="Hello Ada",
            html_body="<p>Hello Ada</p>",
        ),
        core=core,
    )

    assert result.message_id == "provider-message-id"
    assert len(core.messages) == 1
    assert core.messages[0]["sender"].email == "noreply@example.com"
    assert core.messages[0]["sender"].display_name == "Example App"
    assert core.messages[0]["recipient"].email == "ada@example.com"
    assert core.messages[0]["recipient"].display_name == "Ada Lovelace"
    assert core.messages[0]["subject"] == "Hello Ada"
    assert core.messages[0]["body"].html == "<p>Hello Ada</p>"


@pytest.mark.asyncio
async def test_send_auth_email_workflow_runs_end_to_end_under_pytest(
    registered_mock_email_controller: MockWorkflowEmailController,
):
    del registered_mock_email_controller

    config = WorkflowTestConfig.model_construct(RESEND_API_KEY="re_test_key")
    created_cores: list[FakeEmailCore] = []

    async def fake_injection_function(
        config: WorkflowTestConfig = Depends(
            CoreDependencies.get_config_with_type(WorkflowTestConfig)
        ),
    ):
        core = FakeEmailCore(config=config)
        created_cores.append(core)
        yield core

    fake_provider = ProviderDefinition(
        config_class=WorkflowTestConfig,
        core_class=FakeEmailCore,
        injection_function=fake_injection_function,
    )

    with register_config_in_context(config):
        with patch(
            "mountaineer_auth.workflows.send_auth_email.resolve_cloud_by_config",
            return_value=[fake_provider],
        ):
            workflow = SendAuthEmail()
            result = await workflow.run(
                email_key="mock_email",
                email_input={"recipient_name": "Ada"},
                to_email="ada@example.com",
                to_name="Ada Lovelace",
                from_email="noreply@example.com",
                from_name="Example App",
            )

    assert result.message_id == "provider-message-id"
    assert len(created_cores) == 1
    assert created_cores[0].config == config
    assert len(created_cores[0].messages) == 1
    assert created_cores[0].messages[0]["subject"] == "Hello Ada"

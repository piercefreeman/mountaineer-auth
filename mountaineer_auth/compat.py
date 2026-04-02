"""
Compatibility layer to mock other Mountaineer dependencies
to not require their installation for testing.

"""

from importlib import import_module
from typing import Any, cast


def _get_email_workflow_types() -> tuple[Any, Any]:
    try:
        module = cast(Any, import_module("mountaineer_email"))
        return module.SendEmail, module.SendEmailInput
    except (AttributeError, ImportError) as exc:
        raise ImportError(
            "mountaineer-email workflows are not available. "
            "Please install it with: pip install mountaineer-email"
        ) from exc


async def send_email_workflow(
    email_controller,
    email_input,
    *,
    to_email: str,
    to_name: str | None = None,
    from_email: str,
    from_name: str | None = None,
) -> None:
    """
    Send an email using the waymark workflow.

    This is a wrapper that handles the email sending process using waymark's
    workflow system. It runs the SendEmail workflow directly.
    """
    SendEmail, SendEmailInput = _get_email_workflow_types()

    send_email_input = SendEmailInput.from_email_input(
        email_controller,
        email_input=email_input,
        to_email=to_email,
        to_name=to_name,
        from_email=from_email,
        from_name=from_name,
    )

    workflow = SendEmail()
    await workflow.run(
        email_controller=send_email_input.email_controller,
        email_input=send_email_input.email_input.model_dump(mode="json"),
        to_email=str(send_email_input.to_email),
        to_name=send_email_input.to_name,
        from_email=str(send_email_input.from_email),
        from_name=send_email_input.from_name,
    )

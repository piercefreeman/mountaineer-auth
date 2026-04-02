"""
Compatibility layer to mock other Mountaineer dependencies
to not require their installation for testing.

"""

from typing import Any, cast

from mountaineer_email.registry import SerializedEmailController
from mountaineer_email.workflows.send_email import SendEmail, SendEmailInput


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
    send_email_input = SendEmailInput(
        email_controller=email_controller,
        email_input=email_input,
        to_email=to_email,
        to_name=to_name,
        from_email=from_email,
        from_name=from_name,
    )
    serialized_controller = cast(
        SerializedEmailController[Any],
        send_email_input.email_controller,
    )

    workflow = SendEmail()
    await workflow.run(
        email_controller=serialized_controller,
        email_input=send_email_input.email_input,
        to_email=str(send_email_input.to_email),
        to_name=send_email_input.to_name,
        from_email=str(send_email_input.from_email),
        from_name=send_email_input.from_name,
    )

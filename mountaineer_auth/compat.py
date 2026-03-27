"""
Compatibility layer to mock other Mountaineer dependencies
to not require their installation for testing.

"""


async def send_email_workflow(
    email_controller,
    email_input,
) -> None:
    """
    Send an email using the rappel workflow.

    This is a wrapper that handles the email sending process using rappel's
    workflow system. It runs the SendEmail workflow directly.
    """
    try:
        from mountaineer_auth import SendEmail, SendEmailInput
    except ImportError:
        raise ImportError(
            "mountaineer-auth is required to send emails. "
            "Please install it with: pip install mountaineer-auth"
        )

    send_email_input = SendEmailInput.from_email_input(
        email_controller,
        email_input=email_input,
    )

    workflow = SendEmail()
    await workflow.run(
        email_input=send_email_input.email_input,
        registry_id=send_email_input.registry_id,
    )

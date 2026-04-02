"""
Tests for the compatibility layer that provides email workflow support.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSendEmailWorkflow:
    """Tests for send_email_workflow function."""

    @pytest.mark.asyncio
    async def test_sends_email_via_workflow(self):
        """Test that email is sent via the SendEmail workflow."""
        from mountaineer_auth.compat import send_email_workflow

        mock_controller = MagicMock()
        mock_input = MagicMock()

        # Mock the email dependencies
        mock_send_email_input = MagicMock()
        mock_send_email_input.email_controller = {
            "module": "test_module",
            "key": "Test",
        }
        mock_send_email_input.email_input = mock_input
        mock_send_email_input.to_email = "to@example.com"
        mock_send_email_input.to_name = "Ada"
        mock_send_email_input.from_email = "from@example.com"
        mock_send_email_input.from_name = "Example App"

        mock_workflow_instance = MagicMock()
        mock_workflow_instance.run = AsyncMock()
        mock_send_email_input_cls = MagicMock(return_value=mock_send_email_input)
        mock_send_email_cls = MagicMock(return_value=mock_workflow_instance)

        with (
            patch(
                "mountaineer_auth.compat.SendEmailInput",
                mock_send_email_input_cls,
            ),
            patch("mountaineer_auth.compat.SendEmail", mock_send_email_cls),
        ):
            await send_email_workflow(
                mock_controller,
                mock_input,
                to_email="to@example.com",
                to_name="Ada",
                from_email="from@example.com",
                from_name="Example App",
            )

            # Verify the email input was created correctly
            mock_send_email_input_cls.assert_called_once_with(
                email_controller=mock_controller,
                email_input=mock_input,
                to_email="to@example.com",
                to_name="Ada",
                from_email="from@example.com",
                from_name="Example App",
            )

            # Verify the workflow was run
            mock_workflow_instance.run.assert_called_once_with(
                email_controller=mock_send_email_input.email_controller,
                email_input=mock_send_email_input.email_input,
                to_email=mock_send_email_input.to_email,
                to_name=mock_send_email_input.to_name,
                from_email=mock_send_email_input.from_email,
                from_name=mock_send_email_input.from_name,
            )

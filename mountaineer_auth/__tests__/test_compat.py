"""
Tests for the compatibility layer that provides email workflow support.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSendEmailWorkflow:
    """Tests for send_email_workflow function."""

    @pytest.mark.asyncio
    async def test_raises_import_error_when_email_not_installed(self):
        """Test that ImportError is raised when mountaineer-auth is not installed."""
        from mountaineer_auth.compat import send_email_workflow

        mock_controller = MagicMock()
        mock_input = MagicMock()

        with patch("mountaineer_auth.compat.import_module", side_effect=ImportError()):
            with pytest.raises(ImportError) as exc_info:
                await send_email_workflow(
                    mock_controller,
                    mock_input,
                    to_email="to@example.com",
                    from_email="from@example.com",
                )

        assert "mountaineer-auth email workflows are not available" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_sends_email_via_workflow(self):
        """Test that email is sent via the SendEmail workflow."""
        from mountaineer_auth.compat import send_email_workflow

        mock_controller = MagicMock()
        mock_input = MagicMock()

        # Mock the email dependencies
        mock_send_email_input = MagicMock()
        mock_send_email_input.email_input = {"test": "data"}
        mock_send_email_input.email_key = "verify_email"
        mock_send_email_input.to_email = "to@example.com"
        mock_send_email_input.to_name = "Ada"
        mock_send_email_input.from_email = "from@example.com"
        mock_send_email_input.from_name = "Example App"

        mock_workflow_instance = MagicMock()
        mock_workflow_instance.run = AsyncMock()
        mock_send_email_input_cls = MagicMock()
        mock_send_email_input_cls.from_email_input.return_value = mock_send_email_input
        mock_send_email_cls = MagicMock(return_value=mock_workflow_instance)

        with patch(
            "mountaineer_auth.compat._get_email_workflow_types",
            return_value=(mock_send_email_cls, mock_send_email_input_cls),
        ) as mock_from_email_input:
            await send_email_workflow(
                mock_controller,
                mock_input,
                to_email="to@example.com",
                to_name="Ada",
                from_email="from@example.com",
                from_name="Example App",
            )

            mock_from_email_input.assert_called_once_with()

            # Verify the email input was created correctly
            mock_send_email_input_cls.from_email_input.assert_called_once_with(
                mock_controller,
                email_input=mock_input,
                to_email="to@example.com",
                to_name="Ada",
                from_email="from@example.com",
                from_name="Example App",
            )

            # Verify the workflow was run
            mock_workflow_instance.run.assert_called_once_with(
                email_key=mock_send_email_input.email_key,
                email_input=mock_send_email_input.email_input,
                to_email=mock_send_email_input.to_email,
                to_name=mock_send_email_input.to_name,
                from_email=mock_send_email_input.from_email,
                from_name=mock_send_email_input.from_name,
            )

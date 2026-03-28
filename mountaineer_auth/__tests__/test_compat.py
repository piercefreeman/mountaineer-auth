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
        with patch.dict("sys.modules", {"mountaineer_auth": None}):
            # Force re-import of the compat module
            import importlib

            import mountaineer_auth.compat

            importlib.reload(mountaineer_auth.compat)

            mock_controller = MagicMock()
            mock_input = MagicMock()

            with pytest.raises(ImportError) as exc_info:
                await mountaineer_auth.compat.send_email_workflow(
                    mock_controller, mock_input
                )

            assert "mountaineer-auth is required" in str(exc_info.value)

            # Reload to restore original behavior
            importlib.reload(mountaineer_auth.compat)

    @pytest.mark.asyncio
    async def test_sends_email_via_workflow(self):
        """Test that email is sent via the SendEmail workflow."""
        from mountaineer_auth.compat import send_email_workflow

        mock_controller = MagicMock()
        mock_input = MagicMock()

        # Mock the email dependencies
        mock_send_email_input = MagicMock()
        mock_send_email_input.email_input = {"test": "data"}
        mock_send_email_input.registry_id = "test.controller"

        mock_workflow_instance = MagicMock()
        mock_workflow_instance.run = AsyncMock()

        with patch(
            "mountaineer_auth.SendEmailInput.from_email_input",
            return_value=mock_send_email_input,
        ) as mock_from_email_input:
            with patch(
                "mountaineer_auth.SendEmail", return_value=mock_workflow_instance
            ):
                await send_email_workflow(mock_controller, mock_input)

                # Verify the email input was created correctly
                mock_from_email_input.assert_called_once_with(
                    mock_controller, email_input=mock_input
                )

                # Verify the workflow was run
                mock_workflow_instance.run.assert_called_once_with(
                    email_input=mock_send_email_input.email_input,
                    registry_id=mock_send_email_input.registry_id,
                )

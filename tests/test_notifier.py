"""Tests for Notifier."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import apprise

from notifier import Notifier


class TestNotifier:
    """Tests for Notifier class."""
    
    def test_init_with_urls(self):
        """Test Notifier initialization with URLs."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test", "telegram://token/chat"])
            
            assert len(notifier.urls) == 2
            assert mock_apobj.add.call_count == 2
    
    def test_init_without_urls(self):
        """Test Notifier initialization without URLs."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier()
            
            assert notifier.urls == []
            mock_apobj.add.assert_not_called()
    
    def test_init_with_empty_list(self):
        """Test Notifier initialization with empty list."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier([])
            
            assert notifier.urls == []
            mock_apobj.add.assert_not_called()
    
    def test_init_filters_empty_urls(self):
        """Test Notifier filters out empty URL strings."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test", "", None, "telegram://token/chat"])
            
            # Should only add non-empty URLs
            assert mock_apobj.add.call_count == 2
    
    def test_send_success(self):
        """Test successful notification sending."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            result = notifier.send("Test Title", "Test Body", "info")
            
            assert result is True
            mock_apobj.notify.assert_called_once()
            call_args = mock_apobj.notify.call_args
            assert call_args.kwargs['title'] == "Test Title"
            assert call_args.kwargs['body'] == "Test Body"
            assert call_args.kwargs['notify_type'] == apprise.NotifyType.INFO
    
    def test_send_failure(self):
        """Test failed notification sending."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = False
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            result = notifier.send("Test Title", "Test Body")
            
            assert result is False
    
    def test_send_no_urls_configured(self):
        """Test sending notification with no URLs configured."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier([])
            result = notifier.send("Test Title", "Test Body")
            
            # Should return True (success) when no URLs configured
            assert result is True
            # Should not call notify
            mock_apobj.notify.assert_not_called()
    
    @pytest.mark.parametrize("notify_type,expected_apprise_type", [
        ("info", apprise.NotifyType.INFO),
        ("success", apprise.NotifyType.SUCCESS),
        ("warning", apprise.NotifyType.WARNING),
        ("failure", apprise.NotifyType.FAILURE),
    ])
    def test_send_notification_types(self, notify_type, expected_apprise_type):
        """Test different notification types are mapped correctly."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send("Test", "Body", notify_type)
            
            call_args = mock_apobj.notify.call_args
            assert call_args.kwargs['notify_type'] == expected_apprise_type
    
    def test_send_unknown_notification_type(self):
        """Test unknown notification type defaults to INFO."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send("Test", "Body", "unknown_type")
            
            call_args = mock_apobj.notify.call_args
            assert call_args.kwargs['notify_type'] == apprise.NotifyType.INFO
    
    def test_send_exception_handling(self):
        """Test exception handling during notification send."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.side_effect = Exception("Network error")
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            result = notifier.send("Test", "Body")
            
            assert result is False
    
    def test_send_task_success_with_output(self):
        """Test sending task success notification with output."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_success("test-task", 12.5, "Command output here", True)
            
            mock_apobj.notify.assert_called_once()
            call_args = mock_apobj.notify.call_args
            assert "test-task" in call_args.kwargs['title']
            assert "12.5" in call_args.kwargs['body']
            assert "Command output here" in call_args.kwargs['body']
            assert call_args.kwargs['notify_type'] == apprise.NotifyType.SUCCESS
    
    def test_send_task_success_without_output(self):
        """Test sending task success notification without output."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_success("test-task", 5.0, "Some output", False)
            
            call_args = mock_apobj.notify.call_args
            assert "Some output" not in call_args.kwargs['body']
    
    def test_send_task_success_output_truncation(self):
        """Test task success output is truncated to 500 chars."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            long_output = "x" * 1000
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_success("test-task", 1.0, long_output, True)
            
            call_args = mock_apobj.notify.call_args
            body = call_args.kwargs['body']
            # Output should be truncated to 500 chars
            assert long_output[:500] in body
            assert len(body) < len(long_output) + 100  # Account for other text
    
    def test_send_task_failure_with_output(self):
        """Test sending task failure notification with output."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_failure("test-task", "Error occurred", 8.3, True)
            
            mock_apobj.notify.assert_called_once()
            call_args = mock_apobj.notify.call_args
            assert "test-task" in call_args.kwargs['title']
            assert "8.3" in call_args.kwargs['body']
            assert "Error occurred" in call_args.kwargs['body']
            assert call_args.kwargs['notify_type'] == apprise.NotifyType.FAILURE
    
    def test_send_task_failure_without_output(self):
        """Test sending task failure notification without output."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_failure("test-task", "Error", 2.0, False)
            
            call_args = mock_apobj.notify.call_args
            assert "Error" not in call_args.kwargs['body']
    
    def test_send_task_failure_without_duration(self):
        """Test sending task failure notification without duration."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_failure("test-task", "Error", None, True)
            
            call_args = mock_apobj.notify.call_args
            assert "test-task" in call_args.kwargs['title']
            assert "Error" in call_args.kwargs['body']
    
    def test_send_task_failure_output_truncation(self):
        """Test task failure error is truncated to 1000 chars."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            long_error = "e" * 2000
            notifier = Notifier(["discord://test/test"])
            notifier.send_task_failure("test-task", long_error, 1.0, True)
            
            call_args = mock_apobj.notify.call_args
            body = call_args.kwargs['body']
            # Error should be truncated to 1000 chars
            assert long_error[:1000] in body
            assert len(body) < len(long_error) + 100  # Account for other text


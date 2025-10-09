"""Tests for TaskRunner."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import subprocess
import time

from task_runner import TaskRunner
from models import TaskModel, StepModel
from notifier import Notifier


class TestTaskRunner:
    """Tests for TaskRunner class."""
    
    def test_init_with_global_notifier(self, sample_task):
        """Test TaskRunner initialization with global notifier."""
        with patch('notifier.apprise.Apprise'):
            global_notifier = Notifier(["discord://test/test"])
            global_config = {'notify_on': 'all', 'include_output': 'all'}
            
            runner = TaskRunner(sample_task, global_notifier, global_config)
            
            assert runner.name == "test-task"
            assert len(runner.steps) == 1
            assert runner.on_failure == "stop"
            assert runner.retry_count == 3
            assert runner.notify_on == "all"
            assert runner.include_output == "all"
            assert runner.notifier == global_notifier
    
    def test_init_with_task_specific_notifier(self, sample_task):
        """Test TaskRunner uses task-specific notifier when apprise URLs provided."""
        with patch('notifier.apprise.Apprise'):
            sample_task.apprise = ["telegram://token/chat"]
            global_notifier = Notifier(["discord://test/test"])
            global_config = {'notify_on': 'all', 'include_output': 'all'}
            
            runner = TaskRunner(sample_task, global_notifier, global_config)
            
            # Should create its own notifier, not use global
            assert runner.notifier != global_notifier
    
    def test_init_task_overrides_global_notification_settings(self):
        """Test task-specific notification settings override global."""
        with patch('notifier.apprise.Apprise'):
            task = TaskModel(
                name="override-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo test")],
                notify_on="failure",
                include_output="never"
            )
            global_notifier = Notifier(["discord://test/test"])
            global_config = {'notify_on': 'all', 'include_output': 'all'}
            
            runner = TaskRunner(task, global_notifier, global_config)
            
            assert runner.notify_on == "failure"
            assert runner.include_output == "never"
    
    def test_init_defaults_when_no_global_config(self, sample_task):
        """Test TaskRunner uses defaults when no global config provided."""
        with patch('notifier.apprise.Apprise'):
            global_notifier = Notifier([])
            
            runner = TaskRunner(sample_task, global_notifier, None)
            
            assert runner.notify_on == "all"
            assert runner.include_output == "all"
    
    @patch('task_runner.subprocess.run')
    def test_execute_command_success(self, mock_run, sample_task, mock_subprocess_success):
        """Test successful command execution."""
        with patch('notifier.apprise.Apprise'):
            mock_run.return_value = mock_subprocess_success
            global_notifier = Notifier([])
            runner = TaskRunner(sample_task, global_notifier)
            
            success, output = runner._execute_command("echo 'test'")
            
            assert success is True
            assert "Command executed successfully" in output
            mock_run.assert_called_once()
    
    @patch('task_runner.subprocess.run')
    def test_execute_command_failure(self, mock_run, sample_task, mock_subprocess_failure):
        """Test failed command execution."""
        with patch('notifier.apprise.Apprise'):
            mock_run.return_value = mock_subprocess_failure
            global_notifier = Notifier([])
            runner = TaskRunner(sample_task, global_notifier)
            
            success, output = runner._execute_command("false")
            
            assert success is False
            assert "Command failed" in output
    
    @patch('task_runner.subprocess.run')
    def test_execute_command_timeout(self, mock_run, sample_task):
        """Test command execution timeout."""
        with patch('notifier.apprise.Apprise'):
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 3600)
            global_notifier = Notifier([])
            runner = TaskRunner(sample_task, global_notifier)
            
            success, output = runner._execute_command("long_running_command")
            
            assert success is False
            assert "timed out" in output.lower()
    
    @patch('task_runner.subprocess.run')
    def test_execute_command_exception(self, mock_run, sample_task):
        """Test command execution with exception."""
        with patch('notifier.apprise.Apprise'):
            mock_run.side_effect = Exception("Unexpected error")
            global_notifier = Notifier([])
            runner = TaskRunner(sample_task, global_notifier)
            
            success, output = runner._execute_command("bad_command")
            
            assert success is False
            assert "Unexpected error" in output
    
    @patch('task_runner.subprocess.run')
    def test_execute_steps_all_success(self, mock_run, mock_subprocess_success):
        """Test executing multiple steps all succeed."""
        with patch('notifier.apprise.Apprise'):
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="multi-step",
                cron="0 0 * * *",
                steps=[
                    StepModel(command="echo 'step 1'"),
                    StepModel(command="echo 'step 2'"),
                    StepModel(command="echo 'step 3'")
                ]
            )
            global_notifier = Notifier([])
            runner = TaskRunner(task, global_notifier)
            
            success, output = runner._execute_steps()
            
            assert success is True
            assert "Step 1" in output
            assert "Step 2" in output
            assert "Step 3" in output
            assert mock_run.call_count == 3
    
    @patch('task_runner.subprocess.run')
    def test_execute_steps_stop_on_failure(self, mock_run, mock_subprocess_success, mock_subprocess_failure):
        """Test executing steps stops on first failure."""
        with patch('notifier.apprise.Apprise'):
            # First step succeeds, second fails
            mock_run.side_effect = [mock_subprocess_success, mock_subprocess_failure]
            task = TaskModel(
                name="stop-task",
                cron="0 0 * * *",
                steps=[
                    StepModel(command="echo 'step 1'"),
                    StepModel(command="false"),
                    StepModel(command="echo 'step 3'")
                ],
                on_failure="stop"
            )
            global_notifier = Notifier([])
            runner = TaskRunner(task, global_notifier)
            
            success, output = runner._execute_steps()
            
            assert success is False
            assert "Step 1" in output
            assert "Step 2" in output
            # Step 3 should not execute
            assert mock_run.call_count == 2
    
    @patch('task_runner.subprocess.run')
    def test_execute_steps_continue_on_failure(self, mock_run, mock_subprocess_success, mock_subprocess_failure):
        """Test executing steps continues despite failure."""
        with patch('notifier.apprise.Apprise'):
            # Second step fails, but execution continues
            mock_run.side_effect = [mock_subprocess_success, mock_subprocess_failure, mock_subprocess_success]
            task = TaskModel(
                name="continue-task",
                cron="0 0 * * *",
                steps=[
                    StepModel(command="echo 'step 1'"),
                    StepModel(command="false"),
                    StepModel(command="echo 'step 3'")
                ],
                on_failure="continue"
            )
            global_notifier = Notifier([])
            runner = TaskRunner(task, global_notifier)
            
            success, output = runner._execute_steps()
            
            assert success is True
            assert "Step 1" in output
            assert "Step 2" in output
            assert "Step 3" in output
            assert mock_run.call_count == 3
    
    @patch('task_runner.subprocess.run')
    @patch('task_runner.time.sleep')
    def test_execute_steps_retry_success_after_failures(self, mock_sleep, mock_run, 
                                                        mock_subprocess_success, mock_subprocess_failure):
        """Test retry logic succeeds after initial failures."""
        with patch('notifier.apprise.Apprise'):
            # Fail twice, then succeed on third attempt
            mock_run.side_effect = [mock_subprocess_failure, mock_subprocess_failure, mock_subprocess_success]
            task = TaskModel(
                name="retry-task",
                cron="0 0 * * *",
                steps=[StepModel(command="flaky_command")],
                on_failure="retry",
                retry_count=3
            )
            global_notifier = Notifier([])
            runner = TaskRunner(task, global_notifier)
            
            success, output = runner._execute_steps()
            
            assert success is True
            assert mock_run.call_count == 3
            assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('task_runner.subprocess.run')
    @patch('task_runner.time.sleep')
    def test_execute_steps_retry_exhausted(self, mock_sleep, mock_run, mock_subprocess_failure):
        """Test retry logic fails after exhausting all attempts."""
        with patch('notifier.apprise.Apprise'):
            # All attempts fail
            mock_run.return_value = mock_subprocess_failure
            task = TaskModel(
                name="retry-task",
                cron="0 0 * * *",
                steps=[StepModel(command="always_fails")],
                on_failure="retry",
                retry_count=3
            )
            global_notifier = Notifier([])
            runner = TaskRunner(task, global_notifier)
            
            success, output = runner._execute_steps()
            
            assert success is False
            assert mock_run.call_count == 3
            assert mock_sleep.call_count == 2
    
    @patch('task_runner.subprocess.run')
    def test_run_success_sends_notification(self, mock_run, mock_subprocess_success):
        """Test successful task run sends success notification."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="notify-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo 'test'")],
                notify_on="all"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Should send success notification
            assert mock_apobj.notify.called
            call_args = mock_apobj.notify.call_args
            assert "test-task" in call_args.kwargs['title'] or "notify-task" in call_args.kwargs['title']
    
    @patch('task_runner.subprocess.run')
    def test_run_failure_sends_notification(self, mock_run, mock_subprocess_failure):
        """Test failed task run sends failure notification."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_failure
            task = TaskModel(
                name="fail-task",
                cron="0 0 * * *",
                steps=[StepModel(command="false")],
                notify_on="all"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Should send failure notification
            assert mock_apobj.notify.called
            call_args = mock_apobj.notify.call_args
            assert "fail-task" in call_args.kwargs['title']
    
    @patch('task_runner.subprocess.run')
    def test_send_notification_never(self, mock_run, mock_subprocess_success):
        """Test no notification sent when notify_on is 'never'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="silent-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo 'test'")],
                notify_on="never"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Should not send any notification
            mock_apobj.notify.assert_not_called()
    
    @patch('task_runner.subprocess.run')
    def test_send_notification_failure_only_on_success(self, mock_run, mock_subprocess_success):
        """Test no notification on success when notify_on is 'failure'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="failure-only-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo 'test'")],
                notify_on="failure"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Should not send notification on success
            mock_apobj.notify.assert_not_called()
    
    @patch('task_runner.subprocess.run')
    def test_send_notification_failure_only_on_failure(self, mock_run, mock_subprocess_failure):
        """Test notification sent on failure when notify_on is 'failure'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_failure
            task = TaskModel(
                name="failure-only-task",
                cron="0 0 * * *",
                steps=[StepModel(command="false")],
                notify_on="failure"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Should send notification on failure
            assert mock_apobj.notify.called
    
    @patch('task_runner.subprocess.run')
    def test_include_output_all(self, mock_run, mock_subprocess_success):
        """Test output included when include_output is 'all'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="output-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo 'test output'")],
                include_output="all"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Notification should include output
            call_args = mock_apobj.notify.call_args
            assert "Command executed successfully" in call_args.kwargs['body']
    
    @patch('task_runner.subprocess.run')
    def test_include_output_never(self, mock_run, mock_subprocess_success):
        """Test output not included when include_output is 'never'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="no-output-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo 'secret output'")],
                include_output="never"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Notification should not include output
            call_args = mock_apobj.notify.call_args
            assert "secret output" not in call_args.kwargs['body']
    
    @patch('task_runner.subprocess.run')
    def test_include_output_failure_on_success(self, mock_run, mock_subprocess_success):
        """Test output not included on success when include_output is 'failure'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_success
            task = TaskModel(
                name="failure-output-task",
                cron="0 0 * * *",
                steps=[StepModel(command="echo 'output'")],
                include_output="failure"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Notification should not include output on success
            call_args = mock_apobj.notify.call_args
            assert "Command executed successfully" not in call_args.kwargs['body']
    
    @patch('task_runner.subprocess.run')
    def test_include_output_failure_on_failure(self, mock_run, mock_subprocess_failure):
        """Test output included on failure when include_output is 'failure'."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.return_value = mock_subprocess_failure
            task = TaskModel(
                name="failure-output-task",
                cron="0 0 * * *",
                steps=[StepModel(command="false")],
                include_output="failure"
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            runner.run()
            
            # Notification should include output on failure
            call_args = mock_apobj.notify.call_args
            assert "Command failed" in call_args.kwargs['body']
    
    @patch('task_runner.subprocess.run')
    def test_run_exception_handling(self, mock_run):
        """Test task run handles unexpected exceptions."""
        with patch('notifier.apprise.Apprise') as MockApprise:
            mock_apobj = MagicMock()
            mock_apobj.notify.return_value = True
            MockApprise.return_value = mock_apobj
            
            mock_run.side_effect = Exception("Unexpected error")
            task = TaskModel(
                name="error-task",
                cron="0 0 * * *",
                steps=[StepModel(command="bad_command")]
            )
            global_notifier = Notifier(["discord://test/test"])
            runner = TaskRunner(task, global_notifier)
            
            # Should not raise exception
            runner.run()
            
            # Should send failure notification
            assert mock_apobj.notify.called


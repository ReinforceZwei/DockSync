"""Tests for Pydantic models and validation."""

import pytest
from pydantic import ValidationError

from models import (
    StepModel,
    TaskModel,
    NotificationConfigModel,
    ConfigModel
)


class TestStepModel:
    """Tests for StepModel."""
    
    def test_step_model_valid(self):
        """Test creating a valid StepModel."""
        step = StepModel(command="echo 'test'")
        assert step.command == "echo 'test'"
    
    def test_step_model_missing_command(self):
        """Test that StepModel requires command field."""
        with pytest.raises(ValidationError) as exc_info:
            StepModel()
        assert "command" in str(exc_info.value)


class TestTaskModel:
    """Tests for TaskModel."""
    
    def test_task_model_valid(self, sample_step):
        """Test creating a valid TaskModel."""
        task = TaskModel(
            name="test-task",
            cron="0 0 * * *",
            steps=[sample_step]
        )
        assert task.name == "test-task"
        assert task.cron == "0 0 * * *"
        assert len(task.steps) == 1
        assert task.on_failure == "stop"  # Default value
        assert task.retry_count == 3  # Default value
        assert task.notify_on is None
        assert task.include_output is None
        assert task.apprise == []
    
    def test_task_model_with_all_fields(self, sample_step):
        """Test creating a TaskModel with all fields specified."""
        task = TaskModel(
            name="full-task",
            cron="*/30 * * * *",
            steps=[sample_step],
            notify_on="failure",
            include_output="failure",
            on_failure="retry",
            retry_count=5,
            apprise=["discord://test/test"]
        )
        assert task.name == "full-task"
        assert task.notify_on == "failure"
        assert task.include_output == "failure"
        assert task.on_failure == "retry"
        assert task.retry_count == 5
        assert len(task.apprise) == 1
    
    @pytest.mark.parametrize("cron_expr", [
        "0 0 * * *",        # Daily at midnight
        "*/30 * * * *",     # Every 30 minutes
        "0 */6 * * *",      # Every 6 hours
        "0 0 * * 0",        # Weekly on Sunday
        "0 0 1 * *",        # Monthly on 1st
        "0 9 * * 1-5",      # Weekdays at 9 AM
    ])
    def test_task_model_valid_cron_expressions(self, cron_expr, sample_step):
        """Test TaskModel accepts various valid cron expressions."""
        task = TaskModel(
            name="test-task",
            cron=cron_expr,
            steps=[sample_step]
        )
        assert task.cron == cron_expr
    
    @pytest.mark.parametrize("invalid_cron", [
        "invalid",
        "60 0 * * *",       # Invalid minute
        "0 25 * * *",       # Invalid hour
        "0 0 32 * *",       # Invalid day
        "",                 # Empty
        "a b c d e",        # Non-numeric
    ])
    def test_task_model_invalid_cron_expressions(self, invalid_cron, sample_step):
        """Test TaskModel rejects invalid cron expressions."""
        with pytest.raises(ValidationError) as exc_info:
            TaskModel(
                name="test-task",
                cron=invalid_cron,
                steps=[sample_step]
            )
        assert "cron" in str(exc_info.value).lower()
    
    def test_task_model_missing_required_fields(self):
        """Test TaskModel requires name, cron, and steps."""
        with pytest.raises(ValidationError):
            TaskModel()
    
    def test_task_model_empty_steps(self):
        """Test TaskModel requires at least one step."""
        with pytest.raises(ValidationError) as exc_info:
            TaskModel(
                name="test-task",
                cron="0 0 * * *",
                steps=[]
            )
        assert "steps" in str(exc_info.value).lower()
    
    @pytest.mark.parametrize("notify_value", ["all", "failure", "never"])
    def test_task_model_valid_notify_on_values(self, notify_value, sample_step):
        """Test TaskModel accepts valid notify_on values."""
        task = TaskModel(
            name="test-task",
            cron="0 0 * * *",
            steps=[sample_step],
            notify_on=notify_value
        )
        assert task.notify_on == notify_value
    
    def test_task_model_invalid_notify_on(self, sample_step):
        """Test TaskModel rejects invalid notify_on value."""
        with pytest.raises(ValidationError):
            TaskModel(
                name="test-task",
                cron="0 0 * * *",
                steps=[sample_step],
                notify_on="invalid"
            )
    
    @pytest.mark.parametrize("output_value", ["all", "failure", "never"])
    def test_task_model_valid_include_output_values(self, output_value, sample_step):
        """Test TaskModel accepts valid include_output values."""
        task = TaskModel(
            name="test-task",
            cron="0 0 * * *",
            steps=[sample_step],
            include_output=output_value
        )
        assert task.include_output == output_value
    
    def test_task_model_invalid_include_output(self, sample_step):
        """Test TaskModel rejects invalid include_output value."""
        with pytest.raises(ValidationError):
            TaskModel(
                name="test-task",
                cron="0 0 * * *",
                steps=[sample_step],
                include_output="invalid"
            )
    
    @pytest.mark.parametrize("failure_mode", ["stop", "continue", "retry"])
    def test_task_model_valid_on_failure_values(self, failure_mode, sample_step):
        """Test TaskModel accepts valid on_failure values."""
        task = TaskModel(
            name="test-task",
            cron="0 0 * * *",
            steps=[sample_step],
            on_failure=failure_mode
        )
        assert task.on_failure == failure_mode
    
    def test_task_model_invalid_on_failure(self, sample_step):
        """Test TaskModel rejects invalid on_failure value."""
        with pytest.raises(ValidationError):
            TaskModel(
                name="test-task",
                cron="0 0 * * *",
                steps=[sample_step],
                on_failure="invalid"
            )
    
    def test_task_model_retry_count_minimum(self, sample_step):
        """Test TaskModel retry_count must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            TaskModel(
                name="test-task",
                cron="0 0 * * *",
                steps=[sample_step],
                retry_count=0
            )
        assert "retry_count" in str(exc_info.value).lower()
    
    def test_task_model_retry_count_valid(self, sample_step):
        """Test TaskModel accepts valid retry_count values."""
        task = TaskModel(
            name="test-task",
            cron="0 0 * * *",
            steps=[sample_step],
            retry_count=10
        )
        assert task.retry_count == 10


class TestNotificationConfigModel:
    """Tests for NotificationConfigModel."""
    
    def test_notification_config_defaults(self):
        """Test NotificationConfigModel default values."""
        config = NotificationConfigModel()
        assert config.notify_on == "all"
        assert config.include_output == "all"
    
    def test_notification_config_custom_values(self):
        """Test NotificationConfigModel with custom values."""
        config = NotificationConfigModel(
            notify_on="failure",
            include_output="never"
        )
        assert config.notify_on == "failure"
        assert config.include_output == "never"
    
    @pytest.mark.parametrize("notify_value", ["all", "failure", "never"])
    def test_notification_config_valid_notify_on(self, notify_value):
        """Test NotificationConfigModel accepts valid notify_on values."""
        config = NotificationConfigModel(notify_on=notify_value)
        assert config.notify_on == notify_value
    
    def test_notification_config_invalid_notify_on(self):
        """Test NotificationConfigModel rejects invalid notify_on."""
        with pytest.raises(ValidationError):
            NotificationConfigModel(notify_on="invalid")
    
    @pytest.mark.parametrize("output_value", ["all", "failure", "never"])
    def test_notification_config_valid_include_output(self, output_value):
        """Test NotificationConfigModel accepts valid include_output values."""
        config = NotificationConfigModel(include_output=output_value)
        assert config.include_output == output_value
    
    def test_notification_config_invalid_include_output(self):
        """Test NotificationConfigModel rejects invalid include_output."""
        with pytest.raises(ValidationError):
            NotificationConfigModel(include_output="invalid")


class TestConfigModel:
    """Tests for ConfigModel."""
    
    def test_config_model_minimal(self, sample_task):
        """Test ConfigModel with minimal required fields."""
        config = ConfigModel(tasks=[sample_task])
        assert len(config.tasks) == 1
        assert config.apprise == []
        assert config.notification.notify_on == "all"
        assert config.notification.include_output == "all"
    
    def test_config_model_full(self, sample_task):
        """Test ConfigModel with all fields."""
        config = ConfigModel(
            apprise=["discord://test/test", "telegram://token/chat"],
            notification=NotificationConfigModel(
                notify_on="failure",
                include_output="failure"
            ),
            tasks=[sample_task]
        )
        assert len(config.apprise) == 2
        assert config.notification.notify_on == "failure"
        assert config.notification.include_output == "failure"
        assert len(config.tasks) == 1
    
    def test_config_model_multiple_tasks(self, sample_task):
        """Test ConfigModel with multiple tasks."""
        task2 = TaskModel(
            name="task-2",
            cron="*/30 * * * *",
            steps=[StepModel(command="echo 'task 2'")]
        )
        config = ConfigModel(tasks=[sample_task, task2])
        assert len(config.tasks) == 2
        assert config.tasks[0].name == "test-task"
        assert config.tasks[1].name == "task-2"
    
    def test_config_model_no_tasks(self):
        """Test ConfigModel requires at least one task."""
        with pytest.raises(ValidationError) as exc_info:
            ConfigModel(tasks=[])
        assert "tasks" in str(exc_info.value).lower()
    
    def test_config_model_missing_tasks(self):
        """Test ConfigModel requires tasks field."""
        with pytest.raises(ValidationError):
            ConfigModel()


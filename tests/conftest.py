"""Shared pytest fixtures for DockSync tests."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import TaskModel, StepModel, NotificationConfigModel, ConfigModel
from notifier import Notifier
from config_loader import ConfigLoader


@pytest.fixture
def fixture_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_config_path(fixture_dir):
    """Return path to valid config fixture."""
    return str(fixture_dir / "valid_config.yml")


@pytest.fixture
def invalid_config_path(fixture_dir):
    """Return path to invalid config fixture."""
    return str(fixture_dir / "invalid_config.yml")


@pytest.fixture
def minimal_config_path(fixture_dir):
    """Return path to minimal config fixture."""
    return str(fixture_dir / "minimal_config.yml")


@pytest.fixture
def empty_config_path(fixture_dir):
    """Return path to empty config fixture."""
    return str(fixture_dir / "empty_config.yml")


@pytest.fixture
def sample_step():
    """Return a sample StepModel."""
    return StepModel(command="echo 'test'")


@pytest.fixture
def sample_task():
    """Return a sample TaskModel."""
    return TaskModel(
        name="test-task",
        cron="0 0 * * *",
        steps=[StepModel(command="echo 'test'")],
        on_failure="stop",
        retry_count=3
    )


@pytest.fixture
def sample_task_with_retry():
    """Return a sample TaskModel with retry configured."""
    return TaskModel(
        name="retry-task",
        cron="*/30 * * * *",
        steps=[
            StepModel(command="echo 'step 1'"),
            StepModel(command="echo 'step 2'")
        ],
        on_failure="retry",
        retry_count=3,
        notify_on="failure"
    )


@pytest.fixture
def sample_task_with_continue():
    """Return a sample TaskModel with continue on failure."""
    return TaskModel(
        name="continue-task",
        cron="0 2 * * *",
        steps=[
            StepModel(command="echo 'step 1'"),
            StepModel(command="false"),  # This will fail
            StepModel(command="echo 'step 3'")
        ],
        on_failure="continue"
    )


@pytest.fixture
def sample_notification_config():
    """Return a sample NotificationConfigModel."""
    return NotificationConfigModel(
        notify_on="all",
        include_output="all"
    )


@pytest.fixture
def sample_config_model(sample_task):
    """Return a sample ConfigModel."""
    return ConfigModel(
        apprise=["discord://webhook_id/webhook_token"],
        notification=NotificationConfigModel(notify_on="all", include_output="all"),
        tasks=[sample_task]
    )


@pytest.fixture
def mock_apprise():
    """Return a mocked Apprise object."""
    mock = MagicMock()
    mock.notify.return_value = True
    mock.add.return_value = True
    return mock


@pytest.fixture
def mock_notifier(mock_apprise, monkeypatch):
    """Return a Notifier with mocked Apprise."""
    def mock_init(self, urls=None):
        self.apobj = mock_apprise
        self.urls = urls or []
    
    monkeypatch.setattr(Notifier, "__init__", mock_init)
    return Notifier(["discord://test/test"])


@pytest.fixture
def mock_subprocess_success():
    """Return a mock for successful subprocess execution."""
    mock = Mock()
    mock.returncode = 0
    mock.stdout = "Command executed successfully"
    mock.stderr = ""
    return mock


@pytest.fixture
def mock_subprocess_failure():
    """Return a mock for failed subprocess execution."""
    mock = Mock()
    mock.returncode = 1
    mock.stdout = ""
    mock.stderr = "Command failed"
    return mock


@pytest.fixture
def global_notification_config():
    """Return a sample global notification config dictionary."""
    return {
        'notify_on': 'all',
        'include_output': 'all'
    }


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    def _create_config(content: str) -> str:
        config_file = tmp_path / "test_config.yml"
        config_file.write_text(content)
        return str(config_file)
    return _create_config


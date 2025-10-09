"""Tests for ConfigLoader."""

import pytest
from pathlib import Path

from config_loader import ConfigLoader
from models import ConfigModel


class TestConfigLoader:
    """Tests for ConfigLoader class."""
    
    def test_init(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader("/path/to/config.yml")
        assert loader.config_path == "/path/to/config.yml"
        assert loader.config is None
    
    def test_init_default_path(self):
        """Test ConfigLoader with default path."""
        loader = ConfigLoader()
        assert loader.config_path == "/config/config.yml"
    
    def test_load_valid_config(self, valid_config_path):
        """Test loading a valid configuration file."""
        loader = ConfigLoader(valid_config_path)
        config = loader.load()
        
        assert isinstance(config, ConfigModel)
        assert loader.config is not None
        assert len(config.tasks) == 3
        assert len(config.apprise) == 2
        assert config.notification.notify_on == "all"
        assert config.notification.include_output == "all"
    
    def test_load_minimal_config(self, minimal_config_path):
        """Test loading a minimal configuration file."""
        loader = ConfigLoader(minimal_config_path)
        config = loader.load()
        
        assert isinstance(config, ConfigModel)
        assert len(config.tasks) == 1
        assert config.tasks[0].name == "minimal-task"
        assert config.apprise == []
        assert config.notification.notify_on == "all"  # Default
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent configuration file."""
        loader = ConfigLoader("/nonexistent/config.yml")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load()
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_empty_config(self, empty_config_path):
        """Test loading an empty configuration file."""
        loader = ConfigLoader(empty_config_path)
        
        with pytest.raises(ValueError) as exc_info:
            loader.load()
        assert "empty" in str(exc_info.value).lower()
    
    def test_load_invalid_config(self, invalid_config_path):
        """Test loading an invalid configuration file."""
        loader = ConfigLoader(invalid_config_path)
        
        with pytest.raises(ValueError) as exc_info:
            loader.load()
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_load_invalid_yaml_syntax(self, temp_config_file):
        """Test loading a file with invalid YAML syntax."""
        bad_yaml = temp_config_file("""
tasks:
  - name: "test"
    cron: "0 0 * * *"
    steps:
      - command: "echo 'test'"
    invalid_indent:
  wrong indentation
""")
        loader = ConfigLoader(bad_yaml)
        
        with pytest.raises(ValueError) as exc_info:
            loader.load()
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_get_global_apprise_urls_with_urls(self, valid_config_path):
        """Test getting global Apprise URLs when configured."""
        loader = ConfigLoader(valid_config_path)
        loader.load()
        
        urls = loader.get_global_apprise_urls()
        assert len(urls) == 2
        assert "discord://" in urls[0]
        assert "telegram://" in urls[1]
    
    def test_get_global_apprise_urls_no_config(self):
        """Test getting global Apprise URLs before loading config."""
        loader = ConfigLoader("/path/to/config.yml")
        
        urls = loader.get_global_apprise_urls()
        assert urls == []
    
    def test_get_global_apprise_urls_empty(self, minimal_config_path):
        """Test getting global Apprise URLs when none configured."""
        loader = ConfigLoader(minimal_config_path)
        loader.load()
        
        urls = loader.get_global_apprise_urls()
        assert urls == []
    
    def test_get_notification_config_with_config(self, valid_config_path):
        """Test getting notification config when configured."""
        loader = ConfigLoader(valid_config_path)
        loader.load()
        
        notif_config = loader.get_notification_config()
        assert notif_config['notify_on'] == 'all'
        assert notif_config['include_output'] == 'all'
    
    def test_get_notification_config_no_config(self):
        """Test getting notification config before loading."""
        loader = ConfigLoader("/path/to/config.yml")
        
        notif_config = loader.get_notification_config()
        assert notif_config['notify_on'] == 'all'  # Default
        assert notif_config['include_output'] == 'all'  # Default
    
    def test_get_notification_config_defaults(self, minimal_config_path):
        """Test getting notification config with defaults."""
        loader = ConfigLoader(minimal_config_path)
        loader.load()
        
        notif_config = loader.get_notification_config()
        assert notif_config['notify_on'] == 'all'
        assert notif_config['include_output'] == 'all'
    
    def test_get_tasks_with_tasks(self, valid_config_path):
        """Test getting tasks from loaded config."""
        loader = ConfigLoader(valid_config_path)
        loader.load()
        
        tasks = loader.get_tasks()
        assert len(tasks) == 3
        assert tasks[0].name == "test-task-1"
        assert tasks[1].name == "test-task-2"
        assert tasks[2].name == "test-task-3"
    
    def test_get_tasks_no_config(self):
        """Test getting tasks before loading config."""
        loader = ConfigLoader("/path/to/config.yml")
        
        tasks = loader.get_tasks()
        assert tasks == []
    
    def test_load_updates_config_attribute(self, valid_config_path):
        """Test that load() updates the config attribute."""
        loader = ConfigLoader(valid_config_path)
        assert loader.config is None
        
        config = loader.load()
        assert loader.config is not None
        assert loader.config == config
    
    def test_load_task_specific_settings(self, valid_config_path):
        """Test loading tasks with specific notification settings."""
        loader = ConfigLoader(valid_config_path)
        config = loader.load()
        
        # test-task-1 has notify_on explicitly set
        assert config.tasks[0].notify_on == "all"
        
        # test-task-2 has notify_on and include_output set
        assert config.tasks[1].notify_on == "failure"
        assert config.tasks[1].include_output == "failure"
        
        # test-task-3 has task-specific apprise URLs
        assert len(config.tasks[2].apprise) == 1
    
    def test_load_task_failure_strategies(self, valid_config_path):
        """Test loading tasks with different failure strategies."""
        loader = ConfigLoader(valid_config_path)
        config = loader.load()
        
        # test-task-1: on_failure = stop
        assert config.tasks[0].on_failure == "stop"
        
        # test-task-2: on_failure = retry with retry_count
        assert config.tasks[1].on_failure == "retry"
        assert config.tasks[1].retry_count == 3
        
        # test-task-3: on_failure = continue
        assert config.tasks[2].on_failure == "continue"


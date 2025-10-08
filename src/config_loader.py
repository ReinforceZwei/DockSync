"""Configuration loader for DockSync scheduler."""

import os
from typing import List, Dict, Any
from pydantic_yaml import parse_yaml_raw_as
from models import ConfigModel, NotificationConfigModel, TaskModel


class ConfigLoader:
    """Load and validate YAML configuration using Pydantic."""

    def __init__(self, config_path: str = "/config/config.yml"):
        """Initialize config loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config: ConfigModel | None = None

    def load(self) -> ConfigModel:
        """Load and validate configuration from YAML file.
        
        Returns:
            ConfigModel containing validated configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            yaml_content = f.read()

        if not yaml_content.strip():
            raise ValueError("Config file is empty")

        try:
            self.config = parse_yaml_raw_as(ConfigModel, yaml_content)
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")

        return self.config

    def get_global_apprise_urls(self) -> List[str]:
        """Get global Apprise URLs.
        
        Returns:
            List of Apprise URL strings
        """
        if self.config is None:
            return []
        return self.config.apprise
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get global notification configuration.
        
        Returns:
            Dictionary with notification settings (notify_on, include_output)
        """
        if self.config is None:
            return {'notify_on': 'all', 'include_output': 'all'}
        
        return {
            'notify_on': self.config.notification.notify_on,
            'include_output': self.config.notification.include_output
        }

    def get_tasks(self) -> List[TaskModel]:
        """Get all tasks from configuration.
        
        Returns:
            List of TaskModel objects
        """
        if self.config is None:
            return []
        return self.config.tasks


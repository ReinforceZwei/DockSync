"""Configuration loader for DockSync scheduler."""

import yaml
import os
import sys
from typing import Dict, List, Any
from croniter import croniter


class ConfigLoader:
    """Load and validate YAML configuration."""

    def __init__(self, config_path: str = "/config/config.yml"):
        """Initialize config loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = None

    def load(self) -> Dict[str, Any]:
        """Load and validate configuration from YAML file.
        
        Returns:
            Dictionary containing validated configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        if self.config is None:
            raise ValueError("Config file is empty")

        self._validate()
        return self.config

    def _validate(self):
        """Validate configuration structure and values."""
        # Validate apprise URLs (optional)
        if 'apprise' in self.config:
            if not isinstance(self.config['apprise'], list):
                raise ValueError("'apprise' must be a list of URLs")

        # Validate notification settings (optional)
        if 'notification' in self.config:
            self._validate_notification_config(self.config['notification'])

        # Validate tasks
        if 'tasks' not in self.config:
            raise ValueError("Configuration must contain 'tasks' key")

        if not isinstance(self.config['tasks'], list):
            raise ValueError("'tasks' must be a list")

        if len(self.config['tasks']) == 0:
            raise ValueError("At least one task must be defined")

        for idx, task in enumerate(self.config['tasks']):
            self._validate_task(task, idx)
    
    def _validate_notification_config(self, notification: Dict[str, Any]):
        """Validate global notification configuration.
        
        Args:
            notification: Notification configuration dictionary
        """
        if not isinstance(notification, dict):
            raise ValueError("'notification' must be a dictionary")
        
        # Validate notify_on
        if 'notify_on' in notification:
            valid_values = ['all', 'failure', 'never']
            if notification['notify_on'] not in valid_values:
                raise ValueError(
                    f"notification.notify_on must be one of {valid_values}"
                )
        
        # Validate include_output
        if 'include_output' in notification:
            valid_values = ['all', 'failure', 'never']
            if notification['include_output'] not in valid_values:
                raise ValueError(
                    f"notification.include_output must be one of {valid_values}"
                )

    def _validate_task(self, task: Dict[str, Any], idx: int):
        """Validate individual task configuration.
        
        Args:
            task: Task configuration dictionary
            idx: Task index for error messages
        """
        task_id = task.get('name', f'task-{idx}')

        # Validate required fields
        if 'name' not in task:
            raise ValueError(f"Task {idx}: 'name' is required")

        if 'cron' not in task:
            raise ValueError(f"Task '{task_id}': 'cron' is required")

        if 'steps' not in task:
            raise ValueError(f"Task '{task_id}': 'steps' is required")

        # Validate cron expression
        try:
            croniter(task['cron'])
        except Exception as e:
            raise ValueError(f"Task '{task_id}': Invalid cron expression '{task['cron']}': {e}")

        # Validate steps
        if not isinstance(task['steps'], list):
            raise ValueError(f"Task '{task_id}': 'steps' must be a list")

        if len(task['steps']) == 0:
            raise ValueError(f"Task '{task_id}': At least one step must be defined")

        for step_idx, step in enumerate(task['steps']):
            if not isinstance(step, dict):
                raise ValueError(f"Task '{task_id}', step {step_idx}: Step must be a dictionary")
            if 'command' not in step:
                raise ValueError(f"Task '{task_id}', step {step_idx}: 'command' is required")

        # Validate optional fields
        if 'notify_on' in task:
            valid_values = ['all', 'failure', 'never']
            if task['notify_on'] not in valid_values:
                raise ValueError(
                    f"Task '{task_id}': 'notify_on' must be one of {valid_values}"
                )
        
        if 'include_output' in task:
            valid_values = ['all', 'failure', 'never']
            if task['include_output'] not in valid_values:
                raise ValueError(
                    f"Task '{task_id}': 'include_output' must be one of {valid_values}"
                )

        if 'on_failure' in task:
            valid_values = ['stop', 'continue', 'retry']
            if task['on_failure'] not in valid_values:
                raise ValueError(
                    f"Task '{task_id}': 'on_failure' must be one of {valid_values}"
                )

        if 'retry_count' in task:
            if not isinstance(task['retry_count'], int) or task['retry_count'] < 1:
                raise ValueError(
                    f"Task '{task_id}': 'retry_count' must be a positive integer"
                )

        if 'apprise' in task:
            if not isinstance(task['apprise'], list):
                raise ValueError(f"Task '{task_id}': 'apprise' must be a list of URLs")

    def get_global_apprise_urls(self) -> List[str]:
        """Get global Apprise URLs.
        
        Returns:
            List of Apprise URL strings
        """
        return self.config.get('apprise', [])
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get global notification configuration.
        
        Returns:
            Dictionary with notification settings (notify_on, include_output)
        """
        default_config = {
            'notify_on': 'all',
            'include_output': 'all'
        }
        
        if 'notification' in self.config:
            # Merge with defaults
            return {**default_config, **self.config['notification']}
        
        return default_config

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from configuration.
        
        Returns:
            List of task configurations
        """
        return self.config.get('tasks', [])


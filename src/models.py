"""Pydantic models for DockSync configuration."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from croniter import croniter


class StepModel(BaseModel):
    """Model for a single task step."""
    
    command: str = Field(..., description="Shell command to execute")


class TaskModel(BaseModel):
    """Model for a task configuration."""
    
    name: str = Field(..., description="Unique task identifier")
    cron: str = Field(..., description="Cron expression for scheduling")
    steps: List[StepModel] = Field(..., min_length=1, description="Commands to execute")
    notify_on: Optional[Literal['all', 'failure', 'never']] = Field(
        default=None,
        description="When to send notifications (overrides global)"
    )
    include_output: Optional[Literal['all', 'failure', 'never']] = Field(
        default=None,
        description="When to include command output in notifications (overrides global)"
    )
    on_failure: Literal['stop', 'continue', 'retry'] = Field(
        default='stop',
        description="Failure handling strategy"
    )
    retry_count: int = Field(
        default=3,
        ge=1,
        description="Number of retries (if on_failure is 'retry')"
    )
    apprise: List[str] = Field(
        default_factory=list,
        description="Task-specific Apprise URLs (overrides global)"
    )
    
    @field_validator('cron')
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Validate that the cron expression is valid."""
        try:
            croniter(v)
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{v}': {e}")
        return v


class NotificationConfigModel(BaseModel):
    """Model for global notification configuration."""
    
    notify_on: Literal['all', 'failure', 'never'] = Field(
        default='all',
        description="When to send notifications"
    )
    include_output: Literal['all', 'failure', 'never'] = Field(
        default='all',
        description="When to include command output in notifications"
    )


class ConfigModel(BaseModel):
    """Model for the complete DockSync configuration."""
    
    apprise: List[str] = Field(
        default_factory=list,
        description="Global Apprise notification URLs"
    )
    notification: NotificationConfigModel = Field(
        default_factory=NotificationConfigModel,
        description="Global notification settings"
    )
    tasks: List[TaskModel] = Field(
        ...,
        min_length=1,
        description="Task definitions"
    )

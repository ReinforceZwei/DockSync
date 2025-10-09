# DockSync Testing Guide

This document provides detailed information about the testing infrastructure added to DockSync.

## Overview

A comprehensive pytest-based testing framework has been added to ensure code quality and reliability. The test suite covers:

- Configuration loading and validation
- Pydantic model validation
- Task execution with different failure modes
- Notification handling
- Error handling and edge cases

## Test Structure

```
tests/
├── __init__.py                    # Test package marker
├── conftest.py                    # Shared fixtures and test utilities
├── test_models.py                 # Tests for Pydantic models (75+ tests)
├── test_config_loader.py          # Tests for ConfigLoader (20+ tests)
├── test_notifier.py               # Tests for Notifier (25+ tests)
├── test_task_runner.py            # Tests for TaskRunner (30+ tests)
└── fixtures/                      # Test data files
    ├── valid_config.yml           # Valid configuration sample
    ├── minimal_config.yml         # Minimal valid configuration
    ├── invalid_config.yml         # Invalid configuration (for error testing)
    └── empty_config.yml           # Empty file (for error testing)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest>=8.0.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking utilities

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestTaskModel

# Run specific test
pytest tests/test_models.py::TestTaskModel::test_task_model_valid
```

## Test Coverage by Module

### 1. test_models.py (Critical)

Tests Pydantic model validation and constraints:

**StepModel Tests:**
- Valid step creation
- Missing required fields

**TaskModel Tests:**
- Valid task creation with defaults
- All fields specified
- Valid cron expressions (6+ patterns)
- Invalid cron expressions (6+ patterns)
- Empty steps validation
- Valid/invalid `notify_on` values
- Valid/invalid `include_output` values
- Valid/invalid `on_failure` values
- `retry_count` minimum constraint

**NotificationConfigModel Tests:**
- Default values
- Custom values
- Valid/invalid field values

**ConfigModel Tests:**
- Minimal configuration
- Full configuration
- Multiple tasks
- Task requirement validation

### 2. test_config_loader.py (High Priority)

Tests configuration file loading and validation:

**File Loading:**
- Valid configuration files
- Minimal configuration
- Non-existent files (FileNotFoundError)
- Empty files (ValueError)
- Invalid YAML syntax
- Validation failures

**Getter Methods:**
- `get_global_apprise_urls()` with/without URLs
- `get_notification_config()` with/without config
- `get_tasks()` with/without tasks
- Behavior before config is loaded

**Configuration Details:**
- Task-specific notification settings
- Task-specific Apprise URLs
- Different failure strategies

### 3. test_notifier.py (Medium Priority)

Tests notification sending with mocked Apprise:

**Initialization:**
- With URLs
- Without URLs
- Empty URL list
- Filtering empty strings

**Sending Notifications:**
- Successful sends
- Failed sends
- No URLs configured
- Different notification types (info, success, warning, failure)
- Unknown notification types
- Exception handling

**Task Notifications:**
- Success notifications with/without output
- Failure notifications with/without output/duration
- Output truncation (500 chars for success, 1000 for failure)

### 4. test_task_runner.py (High Priority)

Tests task execution with comprehensive scenarios:

**Initialization:**
- With global notifier
- With task-specific notifier
- Task settings override global settings
- Default notification config

**Command Execution:**
- Successful execution
- Failed execution
- Timeout handling
- Exception handling

**Multi-step Execution:**
- All steps succeed
- Stop on failure
- Continue on failure
- Retry logic (success after retries)
- Retry exhausted

**Notification Logic:**
- Success notifications
- Failure notifications
- `notify_on` = "never"
- `notify_on` = "failure" (both success and failure scenarios)
- `include_output` = "all"
- `include_output` = "never"
- `include_output` = "failure" (both success and failure scenarios)

**Error Handling:**
- Unexpected exceptions during task run

## Test Fixtures

### Shared Fixtures (conftest.py)

The `conftest.py` file provides reusable fixtures:

**Path Fixtures:**
- `fixture_dir` - Path to fixtures directory
- `valid_config_path` - Path to valid config
- `invalid_config_path` - Path to invalid config
- `minimal_config_path` - Path to minimal config
- `empty_config_path` - Path to empty config

**Model Fixtures:**
- `sample_step` - Basic StepModel
- `sample_task` - Basic TaskModel
- `sample_task_with_retry` - TaskModel with retry
- `sample_task_with_continue` - TaskModel with continue
- `sample_notification_config` - NotificationConfigModel
- `sample_config_model` - Complete ConfigModel

**Mock Fixtures:**
- `mock_apprise` - Mocked Apprise object
- `mock_notifier` - Notifier with mocked Apprise
- `mock_subprocess_success` - Successful subprocess result
- `mock_subprocess_failure` - Failed subprocess result
- `global_notification_config` - Sample global config dict
- `temp_config_file` - Factory for creating temporary configs

## Writing New Tests

### Best Practices

1. **Use Fixtures**: Leverage shared fixtures from `conftest.py`
2. **Parametrize Tests**: Test multiple scenarios efficiently
3. **Mock External Dependencies**: Use mocks for subprocess, Apprise
4. **Test Edge Cases**: Empty inputs, None values, missing fields
5. **Test Error Handling**: Verify exceptions are raised correctly
6. **Descriptive Names**: Use clear test function names

### Example Test

```python
import pytest
from models import TaskModel, StepModel

def test_task_with_custom_settings(sample_step):
    """Test task with custom notification settings."""
    task = TaskModel(
        name="custom-task",
        cron="0 0 * * *",
        steps=[sample_step],
        notify_on="failure",
        on_failure="retry",
        retry_count=5
    )
    
    assert task.notify_on == "failure"
    assert task.on_failure == "retry"
    assert task.retry_count == 5
```

### Parametrized Test Example

```python
import pytest

@pytest.mark.parametrize("cron,expected", [
    ("0 0 * * *", True),
    ("invalid", False),
])
def test_cron_validation(cron, expected):
    """Test cron expression validation."""
    # Test implementation
    pass
```

## Coverage Goals

- **Overall Coverage**: Aim for 80%+ coverage
- **Critical Modules**: 90%+ coverage for models, config_loader, task_runner
- **Branch Coverage**: Enabled to catch untested code paths

## Running Tests in CI/CD

The test suite is integrated into the GitHub Actions workflow (`.github/workflows/build.yml`):

### Automated Testing

Tests run automatically:
- **On Pull Requests**: All tests must pass before the PR can be merged
- **On Push to Main**: Tests run before building and releasing Docker images
- **Manual Trigger**: Can be triggered via workflow_dispatch

### Workflow Details

The CI/CD pipeline:
1. Sets up Python 3.11
2. Installs all dependencies from `requirements.txt`
3. Runs pytest with coverage reporting
4. Uploads coverage reports to Codecov (optional)
5. Only builds Docker images if all tests pass (on main branch)

### Example Output

When you push code or create a PR, GitHub Actions will:
```
✓ test (ubuntu-latest)
  - Checkout repository
  - Set up Python 3.11
  - Install dependencies
  - Run tests with pytest (109 tests)
  - Upload coverage report

✓ build (ubuntu-latest) [only on main branch]
  - Build and push Docker image
```

### Adding CI/CD to Your Fork

The workflow is already configured in `.github/workflows/build.yml`. To enable Codecov integration:
1. Sign up at [codecov.io](https://codecov.io)
2. Connect your GitHub repository
3. Coverage reports will be automatically uploaded

No additional secrets or configuration required!

## Troubleshooting

### Import Errors

If you see import errors, ensure you're in the project root:

```bash
cd /path/to/DockSync
python -m pytest
```

### Mock Issues

If mocks aren't working correctly, verify patch paths match the import location in the tested module.

### Coverage Not Recording

Ensure pytest is run from the project root and `pytest.ini` is present.

## Future Enhancements

Potential areas for additional testing:

1. **Integration Tests**: End-to-end tests with real Docker containers
2. **Scheduler Tests**: More comprehensive scheduler tests
3. **Performance Tests**: Load testing for high-frequency tasks
4. **Security Tests**: Input validation and sanitization tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)


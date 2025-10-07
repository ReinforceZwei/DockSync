"""Task execution logic for DockSync."""

import subprocess
import logging
import time
from typing import Dict, List, Any, Tuple
from notifier import Notifier

logger = logging.getLogger(__name__)


class TaskRunner:
    """Execute tasks with multi-step support and failure handling."""

    def __init__(self, task_config: Dict[str, Any], global_notifier: Notifier, 
                 global_notification_config: Dict[str, Any] = None):
        """Initialize task runner.
        
        Args:
            task_config: Task configuration dictionary
            global_notifier: Global notifier instance
            global_notification_config: Global notification settings (notify_on, include_output)
        """
        self.config = task_config
        self.name = task_config['name']
        self.steps = task_config['steps']
        self.on_failure = task_config.get('on_failure', 'stop')
        self.retry_count = task_config.get('retry_count', 3)
        
        # Use global notification config as defaults
        if global_notification_config is None:
            global_notification_config = {'notify_on': 'all', 'include_output': 'all'}
        
        # Task can override global notification settings
        self.notify_on = task_config.get('notify_on', global_notification_config.get('notify_on', 'all'))
        self.include_output = task_config.get('include_output', global_notification_config.get('include_output', 'all'))
        
        # Setup notifier (task-specific or global)
        task_apprise_urls = task_config.get('apprise', [])
        if task_apprise_urls:
            self.notifier = Notifier(task_apprise_urls)
        else:
            self.notifier = global_notifier

    def run(self):
        """Execute the task with all its steps."""
        logger.info(f"Starting task: {self.name}")
        start_time = time.time()
        
        try:
            success, output = self._execute_steps()
            duration = time.time() - start_time
            
            if success:
                logger.info(f"Task '{self.name}' completed successfully in {duration:.2f}s")
                self._send_notification(True, duration, output)
            else:
                logger.error(f"Task '{self.name}' failed after {duration:.2f}s")
                self._send_notification(False, duration, output)
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Task '{self.name}' encountered error: {e}")
            self._send_notification(False, duration, str(e))

    def _execute_steps(self) -> Tuple[bool, str]:
        """Execute all steps in the task.
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        all_output = []
        
        for step_idx, step in enumerate(self.steps):
            command = step['command']
            logger.info(f"Task '{self.name}' - Step {step_idx + 1}/{len(self.steps)}: {command}")
            
            attempt = 0
            max_attempts = self.retry_count if self.on_failure == 'retry' else 1
            
            while attempt < max_attempts:
                attempt += 1
                
                try:
                    success, output = self._execute_command(command)
                    all_output.append(f"Step {step_idx + 1}: {command}\n{output}")
                    
                    if success:
                        logger.info(f"Step {step_idx + 1} completed successfully")
                        break
                    else:
                        logger.error(f"Step {step_idx + 1} failed (attempt {attempt}/{max_attempts})")
                        
                        if attempt < max_attempts:
                            # Retry
                            logger.info(f"Retrying step {step_idx + 1}...")
                            time.sleep(2)  # Wait before retry
                            continue
                        
                        # All retries exhausted or no retry configured
                        if self.on_failure == 'stop':
                            logger.error(f"Stopping task '{self.name}' due to step failure")
                            return False, "\n\n".join(all_output)
                        elif self.on_failure == 'continue':
                            logger.warning(f"Continuing task '{self.name}' despite step failure")
                            break
                        else:  # retry exhausted
                            logger.error(f"Task '{self.name}' failed after {max_attempts} retry attempts")
                            return False, "\n\n".join(all_output)
                            
                except Exception as e:
                    logger.error(f"Step {step_idx + 1} error: {e}")
                    all_output.append(f"Step {step_idx + 1}: {command}\nError: {str(e)}")
                    
                    if self.on_failure == 'stop' or (self.on_failure == 'retry' and attempt >= max_attempts):
                        return False, "\n\n".join(all_output)
                    elif self.on_failure == 'continue':
                        break
                    elif attempt < max_attempts:
                        time.sleep(2)
                        continue

        return True, "\n\n".join(all_output)

    def _execute_command(self, command: str) -> Tuple[bool, str]:
        """Execute a single command.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += "\nSTDERR:\n" + result.stderr
            
            success = result.returncode == 0
            
            if not success:
                logger.error(f"Command failed with exit code {result.returncode}")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after 1 hour")
            return False, "Command execution timed out after 1 hour"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return False, f"Execution error: {str(e)}"

    def _send_notification(self, success: bool, duration: float, output: str):
        """Send notification based on task result and settings.
        
        Args:
            success: Whether the task succeeded
            duration: Task duration in seconds
            output: Task output
        """
        # Check if we should send notification
        if self.notify_on == 'never':
            return
        
        if self.notify_on == 'failure' and success:
            return
        
        # Determine if output should be included
        should_include_output = False
        if self.include_output == 'all':
            should_include_output = True
        elif self.include_output == 'failure' and not success:
            should_include_output = True
        # else 'never' or success when 'failure' = False
        
        # Send appropriate notification
        if success:
            self.notifier.send_task_success(self.name, duration, output, should_include_output)
        else:
            self.notifier.send_task_failure(self.name, output, duration, should_include_output)


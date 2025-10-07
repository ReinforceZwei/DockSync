"""Notification wrapper using Apprise."""

import apprise
import logging
from typing import List

logger = logging.getLogger(__name__)


class Notifier:
    """Wrapper for Apprise notification library."""

    def __init__(self, urls: List[str] = None):
        """Initialize notifier with Apprise URLs.
        
        Args:
            urls: List of Apprise URL strings
        """
        self.apobj = apprise.Apprise()
        self.urls = urls or []
        
        for url in self.urls:
            if url:
                self.apobj.add(url)

    def send(self, title: str, body: str, notify_type: str = 'info') -> bool:
        """Send notification to all configured services.
        
        Args:
            title: Notification title
            body: Notification body/message
            notify_type: Type of notification (info, success, warning, failure)
            
        Returns:
            True if at least one notification was sent successfully
        """
        if len(self.urls) == 0:
            logger.debug("No Apprise URLs configured, skipping notification")
            return True

        # Map notify_type to Apprise notification type
        notify_map = {
            'info': apprise.NotifyType.INFO,
            'success': apprise.NotifyType.SUCCESS,
            'warning': apprise.NotifyType.WARNING,
            'failure': apprise.NotifyType.FAILURE,
        }
        
        atype = notify_map.get(notify_type, apprise.NotifyType.INFO)

        try:
            result = self.apobj.notify(
                title=title,
                body=body,
                notify_type=atype
            )
            
            if result:
                logger.info(f"Notification sent successfully: {title}")
            else:
                logger.error(f"Failed to send notification: {title}")
            
            return result
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    def send_task_success(self, task_name: str, duration: float, output: str = "", 
                          include_output: bool = True):
        """Send task success notification.
        
        Args:
            task_name: Name of the completed task
            duration: Task duration in seconds
            output: Optional task output summary
            include_output: Whether to include output in the notification
        """
        title = f"✓ Task Complete: {task_name}"
        body = f"Task '{task_name}' completed successfully in {duration:.2f}s"
        
        if include_output and output:
            body += f"\n\nOutput:\n{output[:500]}"  # Limit output length
        
        self.send(title, body, 'success')

    def send_task_failure(self, task_name: str, error: str, duration: float = None,
                         include_output: bool = True):
        """Send task failure notification.
        
        Args:
            task_name: Name of the failed task
            error: Error message or details
            duration: Optional task duration before failure
            include_output: Whether to include error output in the notification
        """
        title = f"✗ Task Failed: {task_name}"
        body = f"Task '{task_name}' failed"
        
        if duration is not None:
            body += f" after {duration:.2f}s"
        
        if include_output:
            body += f"\n\nError:\n{error[:1000]}"  # Limit error length
        
        self.send(title, body, 'failure')


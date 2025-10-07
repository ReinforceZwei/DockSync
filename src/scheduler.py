"""Main scheduler application for DockSync."""

import logging
import os
import sys
import signal
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config_loader import ConfigLoader
from notifier import Notifier
from task_runner import TaskRunner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


class DockSyncScheduler:
    """Main scheduler application."""

    def __init__(self, config_path: str = "/config/config.yml"):
        """Initialize scheduler.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.scheduler = BackgroundScheduler()
        self.config = None
        self.global_notifier = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.scheduler.shutdown(wait=False)
        sys.exit(0)

    def load_config(self):
        """Load configuration from YAML file."""
        try:
            logger.info(f"Loading configuration from {self.config_path}")
            loader = ConfigLoader(self.config_path)
            self.config = loader.load()
            
            # Initialize global notifier
            global_apprise_urls = loader.get_global_apprise_urls()
            self.global_notifier = Notifier(global_apprise_urls)
            
            # Get global notification config
            self.notification_config = loader.get_notification_config()
            
            logger.info(f"Configuration loaded successfully")
            logger.info(f"Found {len(loader.get_tasks())} task(s)")
            
            if global_apprise_urls:
                logger.info(f"Global Apprise URLs configured: {len(global_apprise_urls)}")
            
            logger.info(f"Global notification settings: notify_on={self.notification_config['notify_on']}, "
                        f"include_output={self.notification_config['include_output']}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def schedule_tasks(self):
        """Schedule all tasks from configuration."""
        tasks = self.config.get('tasks', [])
        
        for task_config in tasks:
            task_name = task_config['name']
            cron_expr = task_config['cron']
            
            try:
                # Create task runner with global notification config
                task_runner = TaskRunner(
                    task_config, 
                    self.global_notifier,
                    self.notification_config
                )
                
                # Parse cron expression
                trigger = CronTrigger.from_crontab(cron_expr)
                
                # Schedule task
                self.scheduler.add_job(
                    task_runner.run,
                    trigger=trigger,
                    id=task_name,
                    name=task_name,
                    max_instances=1,  # Prevent overlapping runs
                    coalesce=True  # Combine missed runs
                )
                
                logger.info(f"Scheduled task '{task_name}' with cron: {cron_expr}")
                
            except Exception as e:
                logger.error(f"Failed to schedule task '{task_name}': {e}")
                sys.exit(1)

    def start(self):
        """Start the scheduler."""
        logger.info("=" * 60)
        logger.info("DockSync - Rclone Scheduler with Notifications")
        logger.info("=" * 60)
        
        self.load_config()
        self.schedule_tasks()
        
        logger.info("Scheduler starting...")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60)
        
        try:
            # Start scheduler in background
            self.scheduler.start()
            
            # Keep the main thread alive with short sleep intervals
            # This allows quick response to Ctrl+C
            while self.running:
                time.sleep(1)
            
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
            self.scheduler.shutdown(wait=False)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.scheduler.shutdown(wait=False)
            sys.exit(1)


def main():
    """Main entry point."""
    # Allow overriding config path via environment variable
    config_path = os.environ.get('DOCKSYNC_CONFIG', '/config/config.yml')
    logger.info(f"Using config path: {config_path}")
    
    scheduler = DockSyncScheduler(config_path)
    scheduler.start()


if __name__ == "__main__":
    main()


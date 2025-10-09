# DockSync

A Docker container to run scheduled rclone tasks and custom scripts with Apprise push notifications.

## Features

- 📅 **Flexible Scheduling**: Define tasks with cron expressions
- 🔄 **Multi-step Tasks**: Execute multiple commands in sequence
- 🔔 **Smart Notifications**: Push notifications via Apprise (supports Discord, Telegram, Slack, email, and [80+ services](https://github.com/caronc/apprise))
- 🛡️ **Failure Handling**: Configure retry, continue, or stop strategies per task
- 🐳 **Docker Native**: Run anywhere Docker runs
- 🗂️ **YAML Configuration**: Simple, readable configuration format
- 📦 **All-in-One**: Includes rclone, Python 3, and common utilities

## Quick Start

### 1. Create Configuration

Create a `config` directory and add your `config.yml`:

```bash
mkdir -p config scripts data
```

Create `config/config.yml` based on the [example configuration](config.example.yml):

```yaml
apprise:
  - "discord://webhook_id/webhook_token"

tasks:
  - name: "daily-backup"
    cron: "0 2 * * *"  # Daily at 2 AM
    notify_on: "all"
    on_failure: "stop"
    steps:
      - command: "rclone sync /data/backup remote:backup"
```

### 2. Add Rclone Configuration

Configure rclone and save the config to `config/rclone.conf`:

```bash
rclone config
# Follow the prompts to configure your remote
```

Or place your existing rclone config at `config/rclone.conf`.

### 3. Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  docksync:
    image: ghcr.io/your-username/docksync:latest
    container_name: docksync
    restart: unless-stopped
    environment:
      - TZ=America/New_York
    volumes:
      - ./config:/config
      - ./scripts:/script
      - ./data:/data
```

Start the container:

```bash
docker-compose up -d
```

### 4. Check Logs

```bash
docker-compose logs -f
```

## Configuration Reference

### Global Settings

#### Apprise URLs

Configure global notification destinations. All tasks will use these unless overridden.

```yaml
apprise:
  - "discord://webhook_id/webhook_token"
  - "telegram://bot_token/chat_id"
  - "email://user:pass@smtp.example.com"
```

See the [Apprise documentation](https://github.com/caronc/apprise) for all supported services and URL formats.

#### Notification Settings

Configure global notification behavior. Tasks can override these settings individually.

```yaml
notification:
  notify_on: "all"          # When to send notifications: all, failure, never
  include_output: "all"     # Include command output: all, failure, never
```

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `notify_on` | string | `all` | `all`, `failure`, `never` | When to send notifications |
| `include_output` | string | `all` | `all`, `failure`, `never` | When to include command output in notifications |

**`notify_on` options:**
- `all`: Send notification for both success and failure
- `failure`: Only send notification on task failure
- `never`: Never send notifications

**`include_output` options:**
- `all`: Include command output in both success and failure notifications
- `failure`: Only include output in failure notifications (success notifications show status only)
- `never`: Never include output (notifications only show task completion status)

### Task Configuration

Each task supports the following options:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | ✅ | - | Unique task identifier |
| `cron` | string | ✅ | - | Cron expression for scheduling |
| `steps` | list | ✅ | - | Commands to execute |
| `notify_on` | string | ❌ | global or `all` | When to notify: `all`, `failure`, `never` (overrides global) |
| `include_output` | string | ❌ | global or `all` | Include output: `all`, `failure`, `never` (overrides global) |
| `on_failure` | string | ❌ | `stop` | Failure strategy: `stop`, `continue`, `retry` |
| `retry_count` | integer | ❌ | `3` | Number of retries (if `on_failure: retry`) |
| `apprise` | list | ❌ | `[]` | Task-specific Apprise URLs (overrides global) |

#### Step Configuration

Each step is a dictionary with a `command` field:

```yaml
steps:
  - command: "rclone sync /data/source remote:dest"
  - command: "/script/custom-script.sh"
  - command: "echo 'Task complete'"
```

### Cron Expression Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

**Common Examples:**

- `0 2 * * *` - Daily at 2:00 AM
- `0 */6 * * *` - Every 6 hours
- `*/30 * * * *` - Every 30 minutes
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 0 1 * *` - Monthly on the 1st at midnight
- `0 9 * * 1-5` - Weekdays at 9:00 AM

## Usage Examples

### Example 1: Simple Daily Backup

```yaml
tasks:
  - name: "daily-backup"
    cron: "0 2 * * *"
    notify_on: "all"
    steps:
      - command: "rclone sync /data/backup remote:backup --progress"
```

### Example 2: Multi-step Archive and Upload

```yaml
tasks:
  - name: "archive-and-upload"
    cron: "0 3 * * 0"  # Weekly on Sunday
    on_failure: "continue"
    steps:
      - command: "tar -czf /data/archive-$(date +%Y%m%d).tar.gz /data/source"
      - command: "rclone copy /data/archive-*.tar.gz remote:archives"
      - command: "/script/cleanup.sh"
```

### Example 3: Task with Retry

```yaml
tasks:
  - name: "sync-with-retry"
    cron: "*/30 * * * *"
    notify_on: "failure"
    on_failure: "retry"
    retry_count: 3
    steps:
      - command: "rclone sync /data/photos remote:photos"
```

### Example 4: Custom Notification per Task

```yaml
tasks:
  - name: "critical-backup"
    cron: "0 */6 * * *"
    apprise:
      - "telegram://bot_token/admin_chat_id"
    steps:
      - command: "rclone sync /data/critical remote:critical-backup"
```

### Example 5: Custom Script

Create `scripts/my-script.sh`:

```bash
#!/bin/bash
echo "Running custom script..."
# Your logic here
```

Make it executable and reference it:

```yaml
tasks:
  - name: "custom-task"
    cron: "0 4 * * *"
    steps:
      - command: "/script/my-script.sh"
```

### Example 6: Control Notification Output

```yaml
# Global settings - include output in all notifications
notification:
  notify_on: "all"
  include_output: "all"

tasks:
  # Task that runs frequently - only notify on failure, no output
  - name: "frequent-sync"
    cron: "*/5 * * * *"
    notify_on: "failure"      # Override: only notify on failure
    include_output: "never"   # Override: never include output
    steps:
      - command: "rclone sync /data/temp remote:temp"
  
  # Critical task - always notify with full output
  - name: "critical-backup"
    cron: "0 2 * * *"
    notify_on: "all"           # Notify on success and failure
    include_output: "failure"  # Only include output on failure
    steps:
      - command: "rclone sync /data/important remote:backup"
```

## Volume Mounts

### Recommended Mount Points

| Mount Point | Purpose | Example |
|-------------|---------|---------|
| `/config` | Configuration files | `./config:/config` |
| `/script` | Custom scripts | `./scripts:/script` |
| `/data` | Data to work on | `./data:/data` |

### Rclone Configuration

Place your rclone config at either:
- `/config/rclone.conf` (custom location)
- `/root/.config/rclone/rclone.conf` (default location)

If using a custom location, set the environment variable:

```yaml
environment:
  - RCLONE_CONFIG=/config/rclone.conf
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `UTC` | Timezone for cron scheduling |
| `DOCKSYNC_CONFIG` | `/config/config.yml` | Path to DockSync configuration file |
| `RCLONE_CONFIG` | - | Custom rclone config path |

### Using Custom Config Location

You can override the default config file location using the `DOCKSYNC_CONFIG` environment variable:

```yaml
# docker-compose.yml
services:
  docksync:
    environment:
      - DOCKSYNC_CONFIG=/config/production-config.yml
    volumes:
      - ./configs/prod.yml:/config/production-config.yml
```

Or when running directly with Docker:

```bash
docker run -e DOCKSYNC_CONFIG=/config/my-config.yml \
  -v ./my-config.yml:/config/my-config.yml \
  ghcr.io/your-username/docksync:latest
```

## Building from Source

```bash
git clone https://github.com/your-username/docksync.git
cd docksync
docker build -t docksync:local .
```

## Apprise Notification Examples

### Discord

1. Create a webhook in your Discord server
2. Add to config:

```yaml
apprise:
  - "discord://webhook_id/webhook_token"
```

### Telegram

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Add to config:

```yaml
apprise:
  - "tgram://bot_token/chat_id"
```

### Slack

```yaml
apprise:
  - "slack://token_a/token_b/token_c"
```

### Email

```yaml
apprise:
  - "mailto://user:pass@smtp.gmail.com?to=recipient@example.com"
```

### Ntfy.sh

```yaml
apprise:
  - "ntfy://ntfy.sh/my_topic"
```

See the [Apprise URL documentation](https://github.com/caronc/apprise/wiki) for all services.

## Troubleshooting

### Check Container Logs

```bash
docker logs docksync
# or
docker-compose logs -f
```

### Validate Configuration

The container will validate your config on startup and show errors if found.

### Test Rclone Connection

```bash
docker exec docksync rclone listremotes
docker exec docksync rclone lsd remote:
```

### Run Task Manually

You can manually trigger a task by executing a command in the container:

```bash
docker exec docksync rclone sync /data/test remote:test
```

### Common Issues

**Task not running at expected time:**
- Verify your cron expression with a [cron calculator](https://crontab.guru/)
- Check the `TZ` environment variable matches your desired timezone
- Review container logs for scheduling confirmation

**Notification not received:**
- Verify Apprise URL format
- Test the Apprise URL using the [Apprise CLI](https://github.com/caronc/apprise)
- Check task `notify_on` setting

**Rclone command fails:**
- Verify rclone config is mounted correctly
- Check remote name in your command matches configured remotes
- Test rclone commands manually with `docker exec`

## Testing

DockSync includes a comprehensive test suite using pytest. The tests cover configuration loading, model validation, task execution, and notification handling.

### Running Tests

#### Install Test Dependencies

```bash
pip install -r requirements.txt
```

#### Run All Tests

```bash
pytest
```

## Contributing

Contributions are welcome! Please open an issue or pull request.

## License

MIT License - see LICENSE file for details

## Related Projects

- [rclone](https://rclone.org/) - rsync for cloud storage
- [Apprise](https://github.com/caronc/apprise) - Push notifications
- [APScheduler](https://apscheduler.readthedocs.io/) - Python scheduling library

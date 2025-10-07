# DockSync - Rclone Scheduler with Notifications
FROM alpine:3.19

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    curl \
    tar \
    zip \
    unzip \
    ca-certificates \
    tzdata

# Install rclone from precompiled binary (latest version)
# Supports multi-architecture builds (amd64, arm64)
ARG TARGETARCH
RUN RCLONE_ARCH=$(case ${TARGETARCH} in \
        amd64) echo "amd64" ;; \
        arm64) echo "arm64" ;; \
        *) echo "amd64" ;; \
    esac) && \
    curl -O https://downloads.rclone.org/rclone-current-linux-${RCLONE_ARCH}.zip && \
    unzip rclone-current-linux-${RCLONE_ARCH}.zip && \
    cd rclone-*-linux-${RCLONE_ARCH} && \
    cp rclone /usr/bin/ && \
    chown root:root /usr/bin/rclone && \
    chmod 755 /usr/bin/rclone && \
    cd .. && \
    rm -rf rclone-*-linux-${RCLONE_ARCH} rclone-current-linux-${RCLONE_ARCH}.zip

# Set environment variables (can be overridden)
ENV TZ=UTC
ENV DOCKSYNC_CONFIG=/config/config.yml
ENV RCLONE_CONFIG=/config/rclone.conf

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ /app/

# Create mount point directories
RUN mkdir -p /config /script /data

# Set Python to run in unbuffered mode for immediate log output
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python3", "/app/scheduler.py"]


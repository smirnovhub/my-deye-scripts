FROM python:3.14-slim

ENV SERVER_PORT=80
ENV MAX_KEYS_COUNT=32
ENV MAX_JSON_SIZE=32768
ENV MAX_JSON_STORAGE_SIZE=262144

# Set username variable
ARG USER_NAME=deyecache

# Set application directory variable
ARG APP_DIR=/home/$USER_NAME

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv

# Install system dependencies: Python, pip, and other tools
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone

# Install required Python packages
RUN pip install --no-cache-dir --break-system-packages fastapi uvicorn uvloop

# Create user without password, with home directory
RUN useradd -m -u 3333 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Set working directory
WORKDIR $APP_DIR

COPY --chown=$USER_NAME:$USER_NAME deyecache/ ./deyecache/

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Expose proxy port
EXPOSE $SERVER_PORT

# Set working directory
WORKDIR $APP_DIR/deyecache

CMD ["python3", "deyecache.py"]

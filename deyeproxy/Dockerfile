FROM python:3.14-slim

ENV LOGGER_HOST=192.168.1.101
ENV LOGGER_PORT=8899
ENV PROXY_PORT=8899
ENV MAX_CONCURRENT_CONNECTIONS=10
ENV CONNECT_TIMEOUT=5
ENV DATA_TIMEOUT=10

# Set username variable
ARG USER_NAME=deyeproxy

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
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone && \
  rm -rf /var/lib/apt/lists/*

# Create user without password, with home directory
RUN useradd -m -u 7777 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Set working directory
WORKDIR $APP_DIR

COPY --chown=$USER_NAME:$USER_NAME deyeproxy/ ./deyeproxy/

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Expose proxy port
EXPOSE $PROXY_PORT

CMD ["python3", "deyeproxy/deyeproxy.py"]

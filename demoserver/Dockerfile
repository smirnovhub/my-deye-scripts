FROM python:3.14-slim

ENV DEYE_LOG_NAME=demoserver

# Set port number to listen on
ARG PORTS="5000 5001"

# Set username variable
ARG USER_NAME=demoserver

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
RUN pip install --no-cache-dir --break-system-packages aiohttp

# Create user without password, with home directory
RUN useradd -m -u 5555 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Set working directory
WORKDIR $APP_DIR

# Copy pre-configured configs to container
COPY --chown=$USER_NAME:$USER_NAME common/ ./common/
COPY --chown=$USER_NAME:$USER_NAME deye/ ./deye/
COPY --chown=$USER_NAME:$USER_NAME modules/ ./modules/
COPY --chown=$USER_NAME:$USER_NAME demoserver/ ./demoserver/

# Set working directory
WORKDIR $APP_DIR/demoserver

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Expose server ports
EXPOSE ${PORTS}

# Starting the bot
CMD ["python3", "demoserver.py"]

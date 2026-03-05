FROM python:3.14-slim

ENV DEYE_LOG_NAME=telebot

# Set remote repository name
ARG REPO_NAME=my-deye-scripts

# Set remote branch name
ARG BRANCH=master

# Set username variable
ARG USER_NAME=telebot

# Set application directory variable
ARG APP_DIR=/home/$USER_NAME

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv

# Install system dependencies: Python, pip, and other tools
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
  tini \
  git && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone

# Install required Python packages
RUN pip install --no-cache-dir --break-system-packages \
  six requests fastapi uvicorn uvloop codespell mypy flake8 \
  types-requests mashumaro

# Copy some useful health scripts like pids guard, etc.
COPY --chmod=755 health/*.sh /usr/local/bin/

# Create user without password, with home directory
RUN useradd -m -u 1111 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Set working directory
WORKDIR $APP_DIR

# Clone the project and initialize submodules
RUN git clone -b $BRANCH https://github.com/smirnovhub/$REPO_NAME.git && \
  cd $REPO_NAME && \
  git submodule update --init --recursive

# Copy pre-configured configs to container
COPY --chown=$USER_NAME:$USER_NAME common/*.py $REPO_NAME/common/

# Set working directory
WORKDIR $APP_DIR/$REPO_NAME

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Use tini as an init process to properly reap zombie processes (PID 1 problem).
# This prevents processes from lingering in a <zombie> state when
# the Python parent doesn't or can't collect their exit status.
ENTRYPOINT ["/usr/bin/tini", "--"]

# Starting the bot
CMD ["python3", "telebot/deyetelebot.py"]

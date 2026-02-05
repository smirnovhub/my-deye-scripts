FROM python:3.14-slim

# Set remote repository name
ARG REPO_NAME=my-deye-scripts

# Set remote branch name
ARG BRANCH=master

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
  apt-get install -y --no-install-recommends \
  git \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone

# Create user without password, with home directory
RUN useradd -m -u 5555 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Install required Python packages
RUN pip install --no-cache-dir six requests

# Set working directory
WORKDIR $APP_DIR

# Clone the project and initialize submodules
RUN git clone -b $BRANCH https://github.com/smirnovhub/$REPO_NAME.git && \
  cd $REPO_NAME && \
  git submodule update --init --recursive

# Copy pre-configured configs to container
COPY demoserver/src/common/*.py $REPO_NAME/common/

# Set working directory
WORKDIR $APP_DIR/$REPO_NAME

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Expose server ports
EXPOSE ${PORTS}

# Starting the bot
CMD ["python3", "demoserver/demoserver"]

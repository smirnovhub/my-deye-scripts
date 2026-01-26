FROM python:3.11-slim

# Set remote repository name
ARG REPO_NAME=my-deye-scripts

# Set username variable
ARG USER_NAME=telebot

# Set application directory variable
ARG APP_DIR=/home/$USER_NAME

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && echo $TIMEZONE > /etc/timezone

# Install git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

# Create symlink so python3 appears in /usr/bin
RUN ln -s /usr/local/bin/python3 /usr/bin/python3 \
 && ln -s /usr/local/bin/pip3 /usr/bin/pip3

# Create user without password, with home directory
RUN useradd -m -u 3333 -s /bin/bash $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Install required Python packages
RUN pip install --no-cache-dir requests

# Set working directory
WORKDIR $APP_DIR

# Clone the project and initialize submodules
RUN git clone https://github.com/smirnovhub/$REPO_NAME.git \
 && cd $REPO_NAME \
 && git submodule update --init --recursive

# Copy pre-configured configs to container
COPY --chown=$USER_NAME:$USER_NAME common/*.py $REPO_NAME/common/

# Set working directory
WORKDIR $APP_DIR/$REPO_NAME

# Starting the bot
CMD ["python3", "telebot/telebot"]

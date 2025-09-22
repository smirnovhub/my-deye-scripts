FROM python:3.11-slim

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && echo $TIMEZONE > /etc/timezone

# Install git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Clone the project from GitHub
RUN git clone https://github.com/smirnovhub/my-deye-scripts.git

# Initialize submodules recursively
RUN cd my-deye-scripts && git submodule update --init --recursive

# Install required Python packages
RUN pip install --no-cache-dir requests

# Copy pre-configured configs to container
COPY deye_loggers.py my-deye-scripts/common/deye_loggers.py
COPY telebot_credentials.py my-deye-scripts/common/telebot_credentials.py
COPY telebot_users.py my-deye-scripts/common/telebot_users.py

# Starting the bot
CMD ["python3", "my-deye-scripts/telebot/telebot"]

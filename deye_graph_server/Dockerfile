FROM python:3.14-slim

ENV DEYE_LOG_NAME=deyegraphserver
ENV SERVER_PORT=80

# Set username variable
ARG USER_NAME=deyegraphserver

# Set application directory variable
ARG APP_DIR=/home/$USER_NAME

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv

# Install system dependencies: Python, pip, and other tools
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
  tini && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone

# Install required Python packages
RUN pip install --no-cache-dir --break-system-packages fastapi uvicorn \
  uvloop pandas matplotlib mashumaro

# Create user without password, with home directory
RUN useradd -m -u 5395 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Set working directory
WORKDIR $APP_DIR

COPY --chown=$USER_NAME:$USER_NAME common/ ./common/
COPY --chown=$USER_NAME:$USER_NAME deye_graph_server/ ./deye_graph_server/

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Expose proxy port
EXPOSE $SERVER_PORT

# Set working directory
WORKDIR $APP_DIR/deye_graph_server

# Use tini as an init process to properly reap zombie processes (PID 1 problem).
# This prevents processes from lingering in a <zombie> state when
# the Python parent doesn't or can't collect their exit status.
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python3", "deye_graph_server.py"]

#!/bin/bash

# Fetch the threshold from environment variable
# Use a default value of 0 to handle cases where it's not set
MAX_HOURS=${RESTART_GUARD_MAX_UPTIME_HOURS:-0}

# Validate: must be a number and greater than or equal to 1
if [[ ! "$MAX_HOURS" =~ ^[0-9]+$ ]] || [ "$MAX_HOURS" -lt 1 ]; then
    echo "RESTART_GUARD_MAX_UPTIME_HOURS is not set or less than 1 ($MAX_HOURS). Skipping check."
    exit 0
fi

# Get the last modification time of /etc/hosts
LAST_MOD_SECONDS=$(stat -c %Y /etc/hosts)
CURRENT_SECONDS=$(date +%s)
AGE_SECONDS=$((CURRENT_SECONDS - LAST_MOD_SECONDS))

# Calculate threshold in seconds
THRESHOLD_SECONDS=$((MAX_HOURS * 3600))

# Logic for killing PID 1
if [ "$AGE_SECONDS" -gt "$THRESHOLD_SECONDS" ]; then
    echo "Container has been running for $AGE_SECONDS seconds (Limit: $THRESHOLD_SECONDS)."
    echo "Killing container..."
    kill -TERM 1
    sleep 15
    kill -KILL 1
else
    # Calculate remaining time for logging
    REMAINING=$(( (THRESHOLD_SECONDS - AGE_SECONDS) / 60 ))
    echo "Uptime OK. Remaining time to restart: $REMAINING minutes."
fi

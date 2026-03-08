#!/bin/bash

# This script monitors the container's process and thread count (PIDs) 
# against the cgroup limits to prevent "RuntimeError: can't start new thread".
# If the count exceeds the threshold, it triggers a graceful shutdown.

# Fail immediately on error
set -e

# Use PIDS_THRESHOLD_PERCENT from env, default to 85 if not set
THRESHOLD_PERCENT=${PIDS_GUARD_THRESHOLD_PERCENT:-85}

# Get the script name without path
SCRIPT_NAME=$(basename "$0")
LOCK_FILE="/var/lock/${SCRIPT_NAME}.lock"

# Open file descriptor 235 for the lock file
exec 235>"$LOCK_FILE"

# Try to get an exclusive lock (non-blocking)
if ! flock -n 235; then
    echo "PIDs guard is already running."
    exit 0
fi

# Detect cgroup v2 or v1
if [ -f /sys/fs/cgroup/pids.current ]; then
    CURRENT=$(cat /sys/fs/cgroup/pids.current)
    MAX=$(cat /sys/fs/cgroup/pids.max)
else
    CURRENT=$(cat /sys/fs/cgroup/pids/pids.current)
    MAX=$(cat /sys/fs/cgroup/pids/pids.max)
fi

# If max is "max" (no limit) — exit OK
if [ "$MAX" = "max" ]; then
    echo "PID limit is set to max. Do nothing."
    exit 0
fi

# Calculate threshold
THRESHOLD=$((MAX * THRESHOLD_PERCENT / 100))

if [ "$CURRENT" -ge "$THRESHOLD" ]; then
    echo "PID limit almost reached ($CURRENT / $MAX). Killing container..."
    kill -TERM 1
    sleep 15
    kill -KILL 1
else
    echo "PID count $CURRENT is below threshold $THRESHOLD ($THRESHOLD_PERCENT%)."
fi

exit 0

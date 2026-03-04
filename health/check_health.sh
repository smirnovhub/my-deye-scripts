#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

bash "$SCRIPT_DIR/pids_guard.sh"
bash "$SCRIPT_DIR/restart_guard.sh"

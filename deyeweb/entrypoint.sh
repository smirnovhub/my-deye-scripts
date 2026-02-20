#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

# Validate that the variable is strictly "true" or "false"
case "${USE_APACHE_BACK_SERVER_PROXY}" in
    "true"|"false")
        echo "USE_APACHE_BACK_SERVER_PROXY is set to ${USE_APACHE_BACK_SERVER_PROXY}"
        ;;
    *)
        echo "Error: USE_APACHE_BACK_SERVER_PROXY must be exactly 'true' or 'false' (case-sensitive)."
        echo "Current value: '${USE_APACHE_BACK_SERVER_PROXY}'"
        exit 1
        ;;
esac

SCRIPT_PATH="/var/www/html/js/script.js"

# Perform the replacement if the file exists
if [ -f "$CONFIG_PATH" ]; then
    # Replace the variable value using the environment variable.
    # We use the variable directly from ENV.
    # Use sed to find the variable and replace its value:
    # [[:space:]]* matches zero or more spaces around the '=' sign
    # [^;]* matches everything between '=' and ';' (the old value)
    sed -i "s/use_apache_proxy_back_endpoint[[:space:]]*=[[:space:]]*[^;]*/use_apache_proxy_back_endpoint = ${USE_APACHE_BACK_SERVER_PROXY}/" "$CONFIG_PATH"
    echo "Successfully updated $CONFIG_PATH"
else
    echo "Error: $CONFIG_PATH not found!"
    exit 1
fi

# Execute the main container process
exec "$@"

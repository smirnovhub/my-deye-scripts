#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

# Fail if DEYE_LOG_NAME is unset or empty
: "${DEYE_LOG_NAME:?Environment variable DEYE_LOG_NAME is not set or empty}"

if [ -n "$BACK_SERVER_URL" ]; then
    echo "Enabling Apache proxy configuration..."
    # Create a symlink from conf-available to conf-enabled
    a2enconf apache-proxy-settings
else
    echo "Disabling Apache proxy configuration..."
    # Ensure it's disabled if the container was restarted with different ENV
    a2disconf -f apache-proxy-settings || true
fi

# Create log directory
mkdir -p "/var/www/html/data/${DEYE_LOG_NAME}"
chown -R www-data:www-data "/var/www/html/data/${DEYE_LOG_NAME}"

# Execute the main container process
exec "$@"

#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

# Validate that the variable is strictly "true" or "false"
case "${USE_BACK_SERVER}" in
    "true"|"false")
        echo "USE_BACK_SERVER is set to ${USE_BACK_SERVER}"
        ;;
    *)
        echo "Error: USE_BACK_SERVER must be exactly 'true' or 'false' (case-sensitive)."
        echo "Current value: '${USE_BACK_SERVER}'"
        exit 1
        ;;
esac

if [ "$USE_BACK_SERVER" = "true" ]; then
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

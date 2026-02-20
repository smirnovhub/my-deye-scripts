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

if [ "$USE_APACHE_BACK_SERVER_PROXY" = "true" ]; then
    echo "Enabling Apache proxy configuration..."
    # Create a symlink from conf-available to conf-enabled
    a2enconf apache-proxy-settings
else
    echo "Disabling Apache proxy configuration..."
    # Ensure it's disabled if the container was restarted with different ENV
    a2disconf -f apache-proxy-settings || true
fi

# Execute the main container process
exec "$@"

#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

# Replace the variable value using the environment variable.
# We use the variable directly from ENV.
# Use sed to find the variable and replace its value:
# [[:space:]]* matches zero or more spaces around the '=' sign
# [^;]* matches everything between '=' and ';' (the old value)
sed -i "s/use_apache_proxy_back_endpoint[[:space:]]*=[[:space:]]*[^;]*/use_apache_proxy_back_endpoint = ${USE_APACHE_BACK_SERVER_PROXY:-false}/" /var/www/html/js/script.js

# This line is crucial: it runs whatever is in CMD
# If CMD is 'httpd-foreground', it will start Apache
exec "$@"

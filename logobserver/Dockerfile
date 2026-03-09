FROM php:8.4-apache

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv

# Install system dependencies
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
  openssl && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone && \
  PHP_EXT_DIR=$(php -i | grep "Scan this dir for additional .ini files" | awk '{print $NF}') && \
  echo "date.timezone = ${TIMEZONE}" > "$PHP_EXT_DIR/timezone.ini" && \
  echo "alias ls='ls --color=auto'" >> /root/.bashrc

# Enable Apache rewrite module (common for PHP apps)
RUN a2enmod rewrite && \
  a2enmod ssl && \
  a2enmod headers

# Generate a self-signed certificate
# -nodes means "no DES" (don't encrypt the private key with a password)
RUN openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/ssl/private/apache-selfsigned.key \
  -out /etc/ssl/certs/apache-selfsigned.crt \
  -subj "/C=UA/L=Kyiv/O=Development/CN=localhost" \
  -addext "basicConstraints=CA:FALSE"
  
# Enable the default SSL configuration of Apache
RUN a2ensite default-ssl

# Point Apache to our new certificates 
# By default, default-ssl uses snakeoil certs, let's point to ours:
RUN sed -i 's|SSLCertificateFile.*|SSLCertificateFile /etc/ssl/certs/apache-selfsigned.crt|' /etc/apache2/sites-available/default-ssl.conf && \
  sed -i 's|SSLCertificateKeyFile.*|SSLCertificateKeyFile /etc/ssl/private/apache-selfsigned.key|' /etc/apache2/sites-available/default-ssl.conf

# Copy and apply configuration
COPY logobserver/apache-docs-settings.conf /etc/apache2/conf-available/apache-docs-settings.conf
RUN a2enconf apache-docs-settings

# Apache runs on ports 80 and 443
EXPOSE 80 443

# The base image already has "CMD [apache2-foreground]"
# so we don't need to redefine it unless we have custom startup logic

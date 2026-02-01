FROM php:8.4-apache AS baseweb

# Set remote repository name
ARG REPO_NAME=my-deye-scripts
ENV REPO_NAME=${REPO_NAME}

# Set remote branch name
ARG BRANCH=master

# Set application directory variable
ARG APP_DIR=/var/www

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv

# Install system dependencies: Python, pip, and other tools
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
#  mc \
#  iputils-ping \
#  traceroute \
#  net-tools \
  git \
  locales \
  openssl \
  python3 \
  python3-pip \
  python3-venv && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone && \
  rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir six requests --break-system-packages

# Generate locales
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
  echo "en_GB.UTF-8 UTF-8" >> /etc/locale.gen && \
  locale-gen

# Set locales
ENV TERM=xterm
ENV EDITOR=mcedit
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_TIME=en_GB.UTF-8

# Add colors to ls command
RUN echo "alias ls='ls --color=auto'" >> /root/.bashrc

# Set working directory
WORKDIR $APP_DIR

# Clone the project and initialize submodules
RUN git clone -b $BRANCH https://github.com/smirnovhub/$REPO_NAME.git && \
  cd $REPO_NAME && \
  git submodule update --init --recursive

# Copy pre-configured configs to container
COPY common/*.py $REPO_NAME/common/

# Create symlink
RUN rm -rf /var/www/html && \
  ln -s $REPO_NAME/deyeweb html

# Enable Apache rewrite module (common for PHP apps)
RUN a2enmod rewrite && \
  a2enmod ssl && \
  a2enmod headers

# Generate a self-signed certificate
# -nodes means "no DES" (don't encrypt the private key with a password)
RUN openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/ssl/private/apache-selfsigned.key \
  -out /etc/ssl/certs/apache-selfsigned.crt \
  -subj "/C=UA/L=Kyiv/O=Development/CN=localhost"

# Enable the default SSL configuration of Apache
RUN a2ensite default-ssl

# (Optional) Point Apache to our new certificates 
# By default, default-ssl uses snakeoil certs, let's point to ours:
RUN sed -i 's|SSLCertificateFile.*|SSLCertificateFile /etc/ssl/certs/apache-selfsigned.crt|' /etc/apache2/sites-available/default-ssl.conf && \
  sed -i 's|SSLCertificateKeyFile.*|SSLCertificateKeyFile /etc/ssl/private/apache-selfsigned.key|' /etc/apache2/sites-available/default-ssl.conf

# Apache runs on ports 80 and 443
EXPOSE 80 443

# Remove installed packages to increase security
RUN apt-get purge -y --auto-remove \
  curl \
  gcc \
  make \
  autoconf \
  libc-dev \
  pkg-config \
  patch \
  binutils && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/*

# The base image already has "CMD [apache2-foreground]"
# so we don't need to redefine it unless we have custom startup logic

###############
### deyeweb ###
###############

FROM baseweb AS deyeweb

# Set proper permissions for Apache
RUN chown -R www-data:www-data $REPO_NAME

###############
### demoweb ###
###############

FROM baseweb AS demoweb

# Copy demo server configs to container
COPY demoserver/src/common/*.py $REPO_NAME/common/

# Set proper permissions for Apache
RUN chown -R www-data:www-data $REPO_NAME

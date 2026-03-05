FROM php:8.4-apache AS baseweb

# Set remote repository name
ARG REPO_NAME=my-deye-scripts
ENV REPO_NAME=${REPO_NAME}
# Set a default value for the backend URL (if backend used)
ENV BACK_SERVER_URL=http://172.17.17.27
# If true we will use apache proxy instead of regular php backend
ENV USE_BACK_SERVER=false

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
  git \
  openssl \
  python3 \
  python3-pip && \
  apt-get purge -y --auto-remove \
  g++ \
  gcc \
  make \
  autoconf \
  libc-dev \
  pkg-config \
  patch \
  binutils && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone && \
  echo "alias ls='ls --color=auto'" >> /root/.bashrc

# Install required Python packages
RUN pip install --no-cache-dir --break-system-packages six requests

# Set working directory
WORKDIR $APP_DIR

# Clone the project and initialize submodules
RUN git clone -b $BRANCH https://github.com/smirnovhub/$REPO_NAME.git && \
  cd $REPO_NAME && \
  git submodule update --init --recursive

# Copy pre-configured configs to container
COPY common/*.py $REPO_NAME/common/

# Find and copy only files from the icons directory to the parent directory
RUN find $REPO_NAME/deyeweb/icons/ -maxdepth 1 -type f -exec cp {} $REPO_NAME/deyeweb/ \;

# Create symlink
RUN rm -rf /var/www/html && \
  ln -s $REPO_NAME/deyeweb html

# Enable Apache rewrite module (common for PHP apps)
RUN a2enmod rewrite && \
  a2enmod ssl && \
  a2enmod headers && \
  a2enmod proxy && \
  a2enmod proxy_http

# Generate a self-signed certificate
# -nodes means "no DES" (don't encrypt the private key with a password)
RUN openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/ssl/private/apache-selfsigned.key \
  -out /etc/ssl/certs/apache-selfsigned.crt \
  -subj "/C=UA/L=Kyiv/O=Development/CN=localhost"

# Comment out the Alias /icons/ directive inside the alias module configuration
# This frees up the /icons/ path for our own application
RUN sed -i 's|^Alias /icons/|#Alias /icons/|' /etc/apache2/mods-available/alias.conf

# Copy proxy configuration
COPY deyeweb/apache/apache-proxy-settings.conf /etc/apache2/conf-available/apache-proxy-settings.conf

# Copy custom logs configuration
# It also includes our ssl configuration
COPY deyeweb/apache/apache-custom-log.conf /etc/apache2/sites-available/apache-custom-log.conf
COPY deyeweb/apache/apache-custom-log-ssl.conf /etc/apache2/sites-available/apache-custom-log-ssl.conf

# Enable our custom logging and ssl certificates
RUN a2dissite 000-default && \
  a2dissite default-ssl && \
  a2ensite apache-custom-log && \
  a2ensite apache-custom-log-ssl

# Copy and prepare the entrypoint script
COPY deyeweb/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set proper permissions for Apache
RUN chown -R www-data:www-data $REPO_NAME

# Apache runs on ports 80 and 443
EXPOSE 80 443

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Use the script as entrypoint
ENTRYPOINT ["entrypoint.sh"]

# Redeclare the default command for php-apache images
CMD ["apache2-foreground"]

###############
### deyeweb ###
###############

FROM baseweb AS deyeweb
ENV DEYE_LOG_NAME=deyeweb

###############
### demoweb ###
###############

FROM baseweb AS demoweb

ENV DEYE_LOG_NAME=demoweb

# Copy demo server configs to container
COPY demoserver/src/common/*.py $REPO_NAME/common/

######################
### deyebackserver ###
######################

FROM python:3.14-slim AS deyebackserver

ENV DEYE_LOG_NAME=backserver
ENV SERVER_PORT=80

# Set remote repository name
ARG REPO_NAME=my-deye-scripts

# Set remote branch name
ARG BRANCH=master

# Set username variable
ARG USER_NAME=backserver

# Set application directory variable
ARG APP_DIR=/home/$USER_NAME

# Set the correct time zone according to your actual location.
# Otherwise, the local time will be incorrect!
ENV TIMEZONE=Europe/Kyiv

# Install system dependencies: Python, pip, and other tools
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
  tini \
  git && \
  apt-get autoremove -y && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* && \
  ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  echo $TIMEZONE > /etc/timezone

# Install required Python packages
RUN pip install --no-cache-dir --break-system-packages \
  six requests fastapi uvicorn uvloop

# Copy some useful health scripts like pids guard, etc.
COPY --chmod=755 health/*.sh /usr/local/bin/

# Create user without password, with home directory
RUN useradd -m -u 7634 -s /usr/sbin/nologin $USER_NAME

# Switch to non-root user
USER $USER_NAME

# Set working directory
WORKDIR $APP_DIR

# Clone the project and initialize submodules
RUN git clone -b $BRANCH https://github.com/smirnovhub/$REPO_NAME.git && \
  cd $REPO_NAME && \
  git submodule update --init --recursive

# Copy pre-configured configs to container
COPY --chown=$USER_NAME:$USER_NAME common/*.py $REPO_NAME/common/

# Expose proxy port
EXPOSE $SERVER_PORT

# Use unbuffered output to see logs in docker logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR $APP_DIR/$REPO_NAME/deyeweb

# Use tini as an init process to properly reap zombie processes (PID 1 problem).
# This prevents processes from lingering in a <zombie> state when
# the Python parent doesn't or can't collect their exit status.
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python3", "backserver.py"]

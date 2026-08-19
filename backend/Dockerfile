FROM php:8.2-cli-alpine

# Install system dependencies & PHP extensions required for Laravel & MySQL
RUN apk add --no-cache \
    curl \
    git \
    libzip-dev \
    zip \
    unzip \
    oniguruma-dev \
    mariadb-client \
    && docker-php-ext-install pdo pdo_mysql mbstring bcmath zip pcntl

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Copy application files
COPY . .

# Install PHP dependencies without dev packages for production
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Create necessary directories and adjust permissions
RUN mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && chmod -R 775 storage bootstrap/cache \
    && chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]

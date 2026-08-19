#!/bin/sh
set -e

echo "==> Running Laravel deployment tasks..."

# Clear old cached configuration
php artisan config:clear || true

# Clear application cache
php artisan cache:clear || true

# Run database migrations
echo "==> Running migrations..."
php artisan migrate --force

# Cache Laravel configuration and routes
echo "==> Caching Laravel configuration..."
php artisan config:cache

echo "==> Caching Laravel routes..."
php artisan route:cache

# Ensure Laravel storage directories exist
echo "==> Preparing storage directories..."
mkdir -p \
    storage/framework/cache \
    storage/framework/sessions \
    storage/framework/views \
    storage/logs \
    bootstrap/cache

chmod -R 775 storage bootstrap/cache || true

# Start Laravel queue worker in background
echo "==> Starting Laravel queue worker..."
php artisan queue:work \
    --sleep=2 \
    --tries=3 \
    --timeout=60 \
    --max-jobs=250 &

# Start Laravel HTTP server
echo "==> Starting Laravel API server on 0.0.0.0:8000..."

exec php -S 0.0.0.0:8000 -t public

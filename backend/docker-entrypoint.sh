#!/bin/sh
set -e

echo "==> Running Laravel deployment tasks..."

# Cache configuration, routes, and views for optimal performance
php artisan config:clear || true
php artisan cache:clear || true

# Run database migrations automatically
echo "==> Running migrations..."
php artisan migrate --force || echo "Warning: Migration failed, check database connectivity."

echo "==> Caching routes and configuration..."
php artisan config:cache || true
php artisan route:cache || true

# Ensure storage directories exist with proper permissions
mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views storage/logs
chmod -R 775 storage bootstrap/cache || true

# Start background queue worker for asynchronous message processing
echo "==> Starting asynchronous queue worker in background..."
php artisan queue:work --sleep=2 --tries=3 --timeout=60 --max-jobs=250 &

# Start PHP built-in web server binding to the dynamically assigned Render port
PORT="${PORT:-8000}"
echo "==> Starting Laravel API server on 0.0.0.0:${PORT}..."
exec php -S 0.0.0.0:${PORT} -t public

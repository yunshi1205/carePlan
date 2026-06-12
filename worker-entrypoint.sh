#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "
import socket, os
s = socket.socket()
s.settimeout(1)
try:
    s.connect((os.environ.get('POSTGRES_HOST', 'db'), int(os.environ.get('POSTGRES_PORT', '5432'))))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
" 2>/dev/null; do
  sleep 1
done

echo "Waiting for Redis..."
while ! python -c "
import socket, os
s = socket.socket()
s.settimeout(1)
try:
    s.connect((os.environ.get('REDIS_HOST', 'redis'), int(os.environ.get('REDIS_PORT', '6379'))))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
" 2>/dev/null; do
  sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Celery worker..."
exec celery -A config worker --loglevel=info -Q careplan

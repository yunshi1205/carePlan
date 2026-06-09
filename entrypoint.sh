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

echo "Running migrations..."
python manage.py migrate --noinput

echo "Loading mock data..."
python manage.py seed_mock_data

echo "Starting Django..."
exec python manage.py runserver 0.0.0.0:8000

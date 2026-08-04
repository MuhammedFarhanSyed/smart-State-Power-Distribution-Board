#!/bin/sh
set -e

echo "Waiting for MySQL database ($DB_HOST:$DB_PORT)..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "MySQL is up and running!"

echo "Running database migrations..."
python manage.py makemigrations network telemetry faults simulator ai_assistant --noinput
python manage.py migrate --noinput

echo "Seeding synthetic electrical network grid..."
python manage.py seed_network --poles=3000

exec "$@"

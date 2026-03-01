#!/bin/bash
set -e

echo "[superset] Running DB migrations..."
superset db upgrade

echo "[superset] Creating admin user..."
superset fab create-admin --username admin --firstname Admin --lastname Admin --email admin@superset.local --password admin 2>/dev/null || echo "[superset] Admin user already exists, skipping."

echo "[superset] Initialising roles and permissions..."
superset init

echo "[superset] Starting server on :8088..."
exec gunicorn --bind 0.0.0.0:8088 --workers 2 --worker-class gthread --threads 2 --timeout 120 --limit-request-line 0 "superset.app:create_app()"

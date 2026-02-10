# Attendance System Backend

[![CI](https://github.com/Larry-007-del/attendance-system-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/Larry-007-del/attendance-system-backend/actions/workflows/ci.yml)

Django REST backend for a mobile attendance system. Designed for Render + Supabase deployment.

## Features

- Django REST API for attendance, courses, students, and staff
- Token authentication (DRF)
- Render-friendly configuration via environment variables
- One-time superuser bootstrap on deploy

## Requirements

- Python 3.11+
- PostgreSQL (Supabase) or SQLite for local dev

## Local Development

1) Create a virtual environment and install dependencies:

   pip install -r requirements.txt

2) Run migrations:

   python manage.py migrate

3) Create a local superuser:

   python manage.py createsuperuser

4) Start the server:

   python manage.py runserver

## Render Deployment (Free Tier)

Render runs without shell access on free tier. This project uses auto-migration and auto-superuser creation on startup.

1) Set environment variables in Render:

   DJANGO_SECRET_KEY=<long-random-secret>
   DEBUG=False
   ALLOWED_HOSTS=your-service.onrender.com
   CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
   DATABASE_URL=<supabase-postgres-connection-string>
   DJANGO_SUPERUSER_USERNAME=<admin_username>
   DJANGO_SUPERUSER_EMAIL=<admin_email>
   DJANGO_SUPERUSER_PASSWORD=<admin_password>
   RESET_BOOTSTRAP_FLAG=False

2) Deploy using render.yaml in the repo root.

## Superuser Bootstrap

- The command ensure_superuser runs at startup.
- It creates or updates the superuser once and records a bootstrap flag.
- To reset the flag on next deploy, set RESET_BOOTSTRAP_FLAG=True for one deploy.

## Notes

- GDAL_LIBRARY_PATH is optional. Only set it if you need GIS features on Linux.
- SQLite is used if DATABASE_URL is not set.

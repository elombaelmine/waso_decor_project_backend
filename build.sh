#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Collect static files safely
python manage.py collectstatic --no-input

# Run database migrations automatically
python manage.py migrate
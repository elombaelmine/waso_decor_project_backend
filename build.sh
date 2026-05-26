#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Collect static files
python manage.py collectstatic --no-input

# 4. Create superuser if it doesn't exist 
# (Only runs if ADMIN_USERNAME is set in your Render Environment Variables)
if [ -n "$ADMIN_USERNAME" ]; then
    python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); \
    User.objects.filter(username='$ADMIN_USERNAME').exists() or \
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')"
fi
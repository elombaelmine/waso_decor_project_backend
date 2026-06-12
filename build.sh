#!/usr/bin/env bash
# Exit on error
set -o errexit

# --- ADD THIS STEP ---
# Upgrade pip to ensure it can find all package versions
pip install --upgrade pip
# ---------------------
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Collect static files
python manage.py collectstatic --no-input

# 4. Create superuser if it doesn't exist 
# (Only runs if ADMIN_USERNAME is set in your Render Environment Variables)
# 4. Create superuser if it doesn't exist AND ensure all users have profiles/OTPs
if [ -n "$ADMIN_USERNAME" ]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model
from main.models import Profile, UserProfileOTP

# Create superuser
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')

# Ensure every user has both a Profile AND an OTP record
for user in User.objects.all():
    Profile.objects.get_or_create(user=user)
    UserProfileOTP.objects.get_or_create(user=user)
"
fi
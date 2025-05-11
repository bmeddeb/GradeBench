#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Function to generate a Django SECRET_KEY
generate_secret_key() {
    python3 - << 'EOF'
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
}

# Function to generate a 32‑byte base64 key for FIELD_ENCRYPTION_KEY
generate_encryption_key() {
    python3 - << 'EOF'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
}

# 1) Create a virtualenv if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2) Install uv if missing and sync dependencies
if ! command -v uv &> /dev/null; then
    echo "'uv' not found. Installing..."
    pip install uv
fi
echo "Installing dependencies..."
uv sync

# 3) Ensure .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "$ENV_FILE not found. Copying from $ENV_EXAMPLE"
    cp "$ENV_EXAMPLE" "$ENV_FILE"
fi

# 4) SECRET_KEY
echo "Enter SECRET_KEY or leave empty to generate one:"
read -r USER_SECRET_KEY
if [ -z "$USER_SECRET_KEY" ]; then
    USER_SECRET_KEY=$(generate_secret_key)
    echo "Generated SECRET_KEY: $USER_SECRET_KEY"
fi
grep -v '^SECRET_KEY=' "$ENV_FILE" > "${ENV_FILE}.tmp"
mv "${ENV_FILE}.tmp" "$ENV_FILE"
echo "SECRET_KEY=$USER_SECRET_KEY" >> "$ENV_FILE"
echo ".env file updated with SECRET_KEY."

# 5) FIELD_ENCRYPTION_KEY
echo "Enter FIELD_ENCRYPTION_KEY or leave empty to generate one:"
read -r USER_ENCRYPTION_KEY
if [ -z "$USER_ENCRYPTION_KEY" ]; then
    USER_ENCRYPTION_KEY=$(generate_encryption_key)
    echo "Generated FIELD_ENCRYPTION_KEY: $USER_ENCRYPTION_KEY"
fi
grep -v '^FIELD_ENCRYPTION_KEY=' "$ENV_FILE" > "${ENV_FILE}.tmp"
mv "${ENV_FILE}.tmp" "$ENV_FILE"
echo "FIELD_ENCRYPTION_KEY=$USER_ENCRYPTION_KEY" >> "$ENV_FILE"
echo ".env file updated with FIELD_ENCRYPTION_KEY."

# 6) Load .env into environment
export DJANGO_SETTINGS_MODULE=gradebench.settings
export $(grep -v '^#' "$ENV_FILE" | xargs)

# 7) Run makemigrations & migrate
echo "Making migrations..."
python manage.py makemigrations
echo "Running migrations..."
python manage.py migrate

# 8) Prompt for GitHub OAuth credentials
while true; do
  echo "Enter GitHub Client ID (GITHUB_KEY) (required):"
  read -r GITHUB_KEY
  [ -n "$GITHUB_KEY" ] && break
  echo "  >> GITHUB_KEY cannot be empty."
done

while true; do
  echo "Enter GitHub Client Secret (GITHUB_SECRET) (required):"
  read -r GITHUB_SECRET
  [ -n "$GITHUB_SECRET" ] && break
  echo "  >> GITHUB_SECRET cannot be empty."
done

grep -v '^GITHUB_KEY=' "$ENV_FILE" > "${ENV_FILE}.tmp"
mv "${ENV_FILE}.tmp" "$ENV_FILE"
echo "GITHUB_KEY=$GITHUB_KEY" >> "$ENV_FILE"

grep -v '^GITHUB_SECRET=' "$ENV_FILE" > "${ENV_FILE}.tmp"
mv "${ENV_FILE}.tmp" "$ENV_FILE"
echo "GITHUB_SECRET=$GITHUB_SECRET" >> "$ENV_FILE"

echo ".env file updated with GitHub OAuth credentials."

# 9) Prompt to create superuser
echo "Would you like to create a Django superuser? [y/N]"
read -r CREATE_SUPERUSER
if [[ "$CREATE_SUPERUSER" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python manage.py createsuperuser
fi

echo "Setup complete."

#!/bin/bash

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Function to generate a Django secret key using Python
generate_secret_key() {
    python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
}

# Function to generate a 32-byte base64 key for FIELD_ENCRYPTION_KEY
generate_encryption_key() {
    python3 -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
}

# Check if uv is installed, install if missing
if ! command -v uv &> /dev/null
then
    echo "'uv' command not found. Installing uv package globally..."
    python3 -m pip install uv
fi

# Create a virtual environment using uv if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment using uv..."
    uv venv
fi

# Activate virtual environment python
source .venv/bin/activate

# Sync dependencies from pyproject.toml using uv
echo "Installing dependencies using uv..."
uv sync

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "$ENV_FILE not found. Creating from $ENV_EXAMPLE"
    cp "$ENV_EXAMPLE" "$ENV_FILE"
fi

# Prompt user for SECRET_KEY or generate automatically
echo "Enter SECRET_KEY or leave empty to generate a secure key:"
read -r USER_SECRET_KEY

if [ -z "$USER_SECRET_KEY" ]; then
    USER_SECRET_KEY=$(generate_secret_key)
    echo "Generated SECRET_KEY: $USER_SECRET_KEY"
fi

# Update or add SECRET_KEY in .env
if grep -q '^SECRET_KEY=' "$ENV_FILE"; then
    sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=$USER_SECRET_KEY/" "$ENV_FILE"
else
    echo "SECRET_KEY=$USER_SECRET_KEY" >> "$ENV_FILE"
fi

echo ".env file updated with SECRET_KEY."

# Prompt user for FIELD_ENCRYPTION_KEY or generate automatically
echo "Enter FIELD_ENCRYPTION_KEY or leave empty to generate a secure key:"
read -r USER_ENCRYPTION_KEY

if [ -z "$USER_ENCRYPTION_KEY" ]; then
    USER_ENCRYPTION_KEY=$(generate_encryption_key)
    echo "Generated FIELD_ENCRYPTION_KEY: $USER_ENCRYPTION_KEY"
fi

# Update or add FIELD_ENCRYPTION_KEY in .env
if grep -q '^FIELD_ENCRYPTION_KEY=' "$ENV_FILE"; then
    sed -i.bak "s/^FIELD_ENCRYPTION_KEY=.*/FIELD_ENCRYPTION_KEY=$USER_ENCRYPTION_KEY/" "$ENV_FILE"
else
    echo "FIELD_ENCRYPTION_KEY=$USER_ENCRYPTION_KEY" >> "$ENV_FILE"
fi

echo ".env file updated with FIELD_ENCRYPTION_KEY."

# Export Django settings module and load env variables for migrate command
export DJANGO_SETTINGS_MODULE=gradebench.settings
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Run makemigrations for all apps
python manage.py makemigrations

# Run migrations
echo "Running Django migrations..."
python manage.py migrate

# Prompt to create superuser
echo "Would you like to create a superuser? [y/N]"
read -r CREATE_SUPERUSER

if [[ "$CREATE_SUPERUSER" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python manage.py createsuperuser
fi

echo "Setup complete."
#!/bin/bash

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Function to generate a Django secret key using Python
generate_secret_key() {
    python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
}

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

# Run migrations
echo "Running Django migrations..."
python3 manage.py migrate

# Prompt to create superuser
echo "Would you like to create a superuser? [y/N]"
read -r CREATE_SUPERUSER

if [[ "$CREATE_SUPERUSER" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python3 manage.py createsuperuser
fi

echo "Setup complete."
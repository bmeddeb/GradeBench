#!/bin/bash

# Activate your virtual environment
source .venv/bin/activate

# Export Django settings module
export DJANGO_SETTINGS_MODULE=gradebench.settings

# Load environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Run Django’s ASGI app with uvicorn
uvicorn gradebench.asgi:application --host 127.0.0.1 --port 8000 --reload
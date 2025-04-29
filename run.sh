#!/bin/bash

# Activate your virtual environment if needed
source .venv/bin/python activate

# Set environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Run Django’s ASGI app with uvicorn
uvicorn gradebench.asgi:application --host 0.0.0.0 --port 8000 --reload
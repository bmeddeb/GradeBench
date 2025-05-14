# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run server**: `python manage.py runserver` or `./run.sh`
- **Install dependencies**: `uv sync`
- **Database migrations**: `python manage.py makemigrations` followed by `python manage.py migrate`
- **Run tests**: `python manage.py test`
- **Run specific test**: `python manage.py test app_name.tests.TestClass.test_method`
- **Linting**: `ruff check --fix`

## Code Style Guidelines

- **Line length**: 88 characters max (per ruff config)
- **Python version**: Target Python 3.13+
- **Imports**: Group by standard library, third-party, then local apps
- **Models**: Include docstrings for model classes; use AsyncModelMixin for async operations
- **Types**: Use type hints consistently (e.g., `from typing import Dict, List, Optional`)
- **Error handling**: Use try/except blocks with specific exceptions and logging
- **Async**: Use Django's asgiref utilities for sync_to_async operations
- **Naming**: Use snake_case for variables/functions, PascalCase for classes
- **Datetime**: Always use timezone-aware datetimes (`from django.utils import timezone`)
- **User timezones**: For displaying dates in templates, use the `user_timezone` template filter: `{{ some_datetime|user_timezone:user|date:"..." }}`
- **Sensitive data**: Use EncryptedCharField for tokens, keys, and credentials
- **UI/UX**: Never use blocking JavaScript alerts/confirms/prompts; use asynchronous notifications (Bootstrap notify, modals, or toast notifications) instead
- **CSS/JavaScript**: Don't add inline CSS/JS to templates; use existing static files in `/static/css/` and `/static/js/` or create new ones. Use variables.css for common values
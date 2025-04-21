# GradeBench

A Django application for grading code submissions with GitHub authentication and async database support.

## Setup and Installation

1. Clone the repository
```
git clone <repository-url>
cd GradeBench
```

2. Set up a virtual environment using UV
```
python -m pip install uv
uv venv
uv pip install -e .
```

3. Configure environment variables
- Copy `.env.example` to `.env` (if not already done)
- Update GitHub credentials in the `.env` file:
  ```
  GITHUB_KEY=your-github-client-id
  GITHUB_SECRET=your-github-client-secret
  ```

4. Run migrations
```
python manage.py migrate
```

5. Create a superuser (optional)
```
python manage.py createsuperuser
```

6. Run the development server
```
python manage.py runserver
```

## GitHub Authentication

To enable GitHub login:

1. Create a GitHub OAuth app at https://github.com/settings/developers
2. Set the Authorization callback URL to: `http://localhost:8000/social-auth/complete/github/`
3. Copy the Client ID and Client Secret to your `.env` file

## Features

- GitHub authentication
- Async database operations
- User profile with GitHub integration
- Modern Bootstrap 5 UI

## Technology Stack

- Django 5.2+
- Python 3.13+
- UV for package management
- Databases[sqlite] for async database operations
- Social Auth App for GitHub authentication
- Bootstrap 5 for UI

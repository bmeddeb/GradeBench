# GradeBench

GradeBench is a platform that integrates different service providers (Git platforms, project management tools, and learning management systems) to simplify the grading process for programming courses.

## Project Structure

GradeBench uses a domain-based structure organized by provider type:

```
gradebench/
├─ core/                      # Core functionality and shared components
├─ git_providers/             # Git repository platform integrations
│  ├─ common/                 # Shared code for all git providers
│  ├─ github/                 # GitHub specific implementation
│  └─ ...                     # Other git platforms
├─ project_mgmt/              # Project management tool integrations
│  ├─ common/                 # Shared code for all project management tools
│  ├─ taiga/                  # Taiga specific implementation
│  └─ ...                     # Other project management tools
├─ lms/                       # Learning Management System integrations
│  ├─ common/                 # Shared code for all LMS platforms
│  ├─ canvas/                 # Canvas specific implementation
│  └─ ...                     # Other LMS platforms
├─ integrations/              # Cross-domain integrations and connections
```

For detailed documentation on the structure, see [dev_docs/structure.md](dev_docs/structure.md).

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gradebench.git
   cd gradebench
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure your database in `settings.py`

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

## Configuration

See [dev_docs/settings_update.md](dev_docs/settings_update.md) for details on configuring the application.

## Features

- Integration with multiple Git platforms (GitHub, etc.)
- Integration with project management tools (Taiga, etc.)
- Integration with learning management systems (Canvas, etc.)
- Unified interface for grading student work
- Asynchronous processing for better performance

## Contributing

If you'd like to contribute to GradeBench, please:

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

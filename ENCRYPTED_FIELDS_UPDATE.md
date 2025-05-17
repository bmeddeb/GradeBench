# EncryptedCharField Help Text Update

## Summary

Added help text to all EncryptedCharField instances across the codebase to improve user understanding of these secure fields.

## Changes Made

### Core App (`core/models.py`)
1. **UserProfile.github_access_token**
   - Added: `"Encrypted GitHub personal access token for API authentication"`

2. **GitHubToken.token**
   - Added: `"Encrypted GitHub API token"`

3. **StaffProfile.lms_access_token**
   - Added: `"Encrypted Learning Management System (LMS) API access token"`

4. **StaffProfile.lms_refresh_token**
   - Added: `"Encrypted LMS API refresh token for obtaining new access tokens"`

### LMS App (`lms/canvas/models.py`)
1. **CanvasIntegration.api_key**
   - Added: `"Encrypted Canvas API key for authentication"`

2. **CanvasIntegration.refresh_token**
   - Added: `"Encrypted Canvas OAuth2 refresh token"`

## Next Steps

1. Apply the migrations:
   ```bash
   python manage.py migrate
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "Add help text to all EncryptedCharField instances"
   ```

## Benefits

- Users will now see descriptive help text in the Django admin and forms
- Clear indication that these fields are securely encrypted
- Better understanding of what each token/key is used for
# Canvas API: Cracking the code to course retrieval

Getting a list of courses from the Canvas API is one of the most common operations for Canvas integrations. This guide provides everything you need to make these API calls effectively, from authentication to code examples.

## The bottom line

The Canvas API offers multiple endpoints for retrieving courses with `/api/v1/courses` being the most commonly used. Authentication requires either an API token (via `Authorization: Bearer <token>` header) or OAuth2. All course listing endpoints support filters like enrollment state, term, and course status. Pagination is handled through Link headers with a default limit of 10 items per page. Libraries like CanvasAPI (Python), @kth/canvas-api (JavaScript), and Pandarus (Ruby) simplify working with the API by handling authentication, pagination, and error handling automatically.

## Authentication methods

### API token authentication

This is the simplest method, ideal for testing and personal tools:

```
Authorization: Bearer <token>
```

Users generate tokens in their Canvas account under Settings → New Access Token. These tokens have the same permissions as the user who created them.

**Example header:**
```
Authorization: Bearer 1~aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT
```

### OAuth2 authentication

For multi-user applications, OAuth2 is required:

1. Register a Developer Key with Canvas to get a client ID and secret
2. Implement the OAuth2 authorization flow:
   - Redirect users to `/login/oauth2/auth` with your client_id and redirect_uri
   - Canvas redirects back with an authorization code
   - Exchange code for token with POST to `/login/oauth2/token`

The response includes an access token, refresh token, and user information:

```json
{
  "access_token": "1/fFAGRNJru1FTz70BzhT3Zg",
  "token_type": "Bearer",
  "user": {"id": 42, "name": "Jimi Hendrix"},
  "refresh_token": "tIh2YBWGiC0GgGRglT9Ylwv2MnTvy8csf...",
  "expires_in": 3600
}
```

## Course listing endpoints

Canvas provides several endpoints for retrieving courses, each serving different use cases:

| Endpoint | Description | Permissions |
|----------|-------------|------------|
| `GET /api/v1/courses` | Lists courses for the current user | Available to all users |
| `GET /api/v1/users/:user_id/courses` | Lists courses for a specific user | Requires being that user, an observer, or admin |
| `GET /api/v1/accounts/:account_id/courses` | Lists all courses in an account | Requires admin access |
| `GET /api/v1/courses/:id` | Gets a single course | Requires enrollment in the course |

## Parameters for filtering courses

When retrieving courses, you can use various parameters to filter the results:

### Common parameters

- `enrollment_type`: Filter by role ("teacher", "student", "ta", "observer", "designer")
- `enrollment_state`: Filter by enrollment state ("active", "invited", "completed", etc.)
- `state[]`: Filter by course state ("unpublished", "available", "completed", "deleted")
- `include[]`: Additional data to include in the response (multiple values allowed)

### Account-specific parameters

When using `/api/v1/accounts/:account_id/courses`, additional filters are available:

- `enrollment_term_id`: Filter by term
- `search_term`: Text search for course name or code
- `published`: Filter for published courses only
- `completed`: Filter for completed courses
- `blueprint`: Filter for blueprint courses
- `by_teachers[]`: Filter by teacher IDs
- `starts_before`/`starts_after`/`ends_before`/`ends_after`: Date filtering

## Example API calls and responses

### Basic course listing

```
GET /api/v1/courses
Authorization: Bearer <token>
```

Response:
```json
[
  {
    "id": 1234,
    "name": "Introduction to Computer Science",
    "course_code": "CS-101",
    "start_at": "2025-01-15T00:00:00Z",
    "end_at": "2025-05-15T00:00:00Z",
    "enrollment_term_id": 1,
    "uuid": "abcdef12-3456-7890-abcd-ef1234567890",
    "is_public": false,
    "created_at": "2024-12-01T00:00:00Z",
    "default_view": "syllabus",
    "root_account_id": 1,
    "license": "private",
    "storage_quota_mb": 500
  }
]
```

### Filtered course listing

```
GET /api/v1/courses?enrollment_state=active&include[]=term&include[]=total_students
Authorization: Bearer <token>
```

### Account courses with term filter

```
GET /api/v1/accounts/1/courses?enrollment_term_id=2&state[]=available&with_enrollments=true
Authorization: Bearer <token>
```

## Pagination handling

The Canvas API uses the Link header for pagination. By default, responses contain 10 items per page, adjustable with the `per_page` parameter (up to 100).

**Sample Link header:**
```
Link: <https://canvas.example.edu/api/v1/courses?page=2>; rel="next", 
      <https://canvas.example.edu/api/v1/courses?page=1>; rel="first", 
      <https://canvas.example.edu/api/v1/courses?page=5>; rel="last"
```

To retrieve all courses, follow these links until no "next" link is provided.

## Code examples

### Python with CanvasAPI library

```python
from canvasapi import Canvas

# Initialize a new Canvas object
API_URL = "https://canvas.example.edu"
API_KEY = "your_api_key"
canvas = Canvas(API_URL, API_KEY)

# Get courses for the current user
courses = canvas.get_courses()
for course in courses:
    print(f"Course: {course.name} (ID: {course.id})")
    
# Filter courses with parameters
active_courses = canvas.get_courses(enrollment_state='active')
for course in active_courses:
    print(f"Active course: {course.name}")

# Get courses for a specific user
user = canvas.get_user(123)
user_courses = user.get_courses()

# Get courses in an account (admin only)
account = canvas.get_account(1)
account_courses = account.get_courses()
```

### JavaScript with fetch API

```javascript
const API_URL = "https://canvas.example.edu/api/v1";
const API_TOKEN = "your_api_token";

const headers = {
  "Authorization": `Bearer ${API_TOKEN}`
};

// Function to get all courses with pagination handling
async function getAllCourses() {
  let url = `${API_URL}/courses?per_page=100`;
  const allCourses = [];
  
  while (url) {
    try {
      const response = await fetch(url, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const courses = await response.json();
      allCourses.push(...courses);
      
      // Check for Link header to handle pagination
      const linkHeader = response.headers.get('Link');
      url = null; // Default to null if no next page
      
      if (linkHeader) {
        // Parse Link header to find next URL
        const links = linkHeader.split(',');
        for (const link of links) {
          if (link.includes('rel="next"')) {
            url = link.split(';')[0].replace(/[<>]/g, '');
            break;
          }
        }
      }
    } catch (error) {
      console.error("Error fetching courses:", error);
      break;
    }
  }
  
  return allCourses;
}

// Usage
getAllCourses().then(courses => {
  courses.forEach(course => {
    console.log(`Course: ${course.name} (ID: ${course.id})`);
  });
});
```

### Ruby with Pandarus library

```ruby
require 'pandarus'

# Initialize the client
client = Pandarus::Client.new(
  prefix: 'https://canvas.example.edu/api',
  token: 'your_api_token'
)

# Get a single course
course = client.get_single_course(1234)
puts "Course: #{course.name} (ID: #{course.id})"

# Get all courses with pagination handling
courses = client.list_courses
courses.each do |course|
  puts "Course: #{course.name} (ID: #{course.id})"
end

# Get courses from an account
account_courses = client.list_active_courses_in_account(1)
```

## How pagination works

Canvas uses a "Link" HTTP header to provide pagination controls, following the [RFC 5988](https://tools.ietf.org/html/rfc5988) specification.

When implementing pagination handling, remember:

1. **Use the Link header**: Don't try to construct pagination URLs manually
2. **Append authentication**: The Link header URLs don't include access tokens
3. **Check for "next" link**: The absence of a "next" link indicates the last page
4. **Adjust page size**: Use `per_page=100` to reduce the number of API calls

Libraries like CanvasAPI (Python) and @kth/canvas-api (JavaScript) handle pagination automatically.

## Best practices for Canvas API integration

1. **Use official libraries** when available:
   - Python: [CanvasAPI](https://github.com/ucfopen/canvasapi)
   - JavaScript: [@kth/canvas-api](https://github.com/KTH/canvas-api)
   - Ruby: [Pandarus](https://github.com/instructure/pandarus)

2. **Handle authentication securely**:
   - Store API tokens in environment variables, not in code
   - Use OAuth2 for multi-user applications
   - Never store tokens in client-side code

3. **Respect rate limits**:
   - Canvas uses a "leaky bucket" algorithm (about 700 units before throttling)
   - Monitor the `X-Rate-Limit-Remaining` header
   - Implement exponential backoff when throttled (HTTP 403)

4. **Implement robust error handling**:
   - 400 Bad Request: Invalid parameters
   - 401 Unauthorized: Authentication failed
   - 403 Forbidden: Insufficient permissions or rate limited
   - 404 Not Found: Resource doesn't exist
   - 429 Too Many Requests: Rate limit exceeded

5. **Optimize request volume**:
   - Use `include[]` to fetch related data in a single request
   - Set `per_page=100` to reduce pagination requests
   - Filter results server-side using query parameters

## Common pitfalls to avoid

1. **Ignoring pagination**: Always check for and follow pagination links
2. **Over-requesting**: Avoid polling the API too frequently
3. **ID handling issues**: Large integer IDs can cause problems in some languages
   - Use `Accept: application/json+canvas-string-ids` header to convert IDs to strings
4. **Insufficient error handling**: Always implement proper error handling and retries
5. **Exposing tokens**: Never expose API tokens in client-side code or repositories

By following these guidelines and leveraging the code examples provided, you can effectively integrate with the Canvas API to retrieve course information for your applications.
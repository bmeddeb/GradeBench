# Canvas LMS — Grouping Endpoints

When instructors organize students into groups or group‐sets, you can discover that structure via the following Canvas REST API endpoints:

---

## 1. Group Categories (“Group Sets”)

- **List all group categories in a course**  
  ```http
  GET /api/v1/courses/:course_id/group_categories


- **(Alternative) List group categories in an account**  
  ```http request
    GET /api/v1/accounts/:account_id/group_categories
    ```

Returns all group categories at the account level

## 2. Groups 

- **List all groups in a course**
```http request
GET /api/v1/courses/:course_id/groups
```
Returns every group (across all group categories plus any “community” groups) for that course.

- **List groups in a specific category**
```http request
GET /api/v1/group_categories/:group_category_id/groups
```
Returns just the groups belonging to the given category (i.e. the individual teams within that “group set”). 

- **Get a single group’s details**
```http request
GET /api/v1/groups/:group_id
```
Fetch metadata (name, description, join_level, etc.) for one group.

## 3. Group Memberships
- **List all users in a group category**
```http request
GET /api/v1/group_categories/:group_category_id/users
```
Returns every user assigned to any group in that category (optionally filter unassigned=true).

- **List members of a specific group**
```http request
GET /api/v1/groups/:group_id/users
```
Returns the users in that particular group (with their user info, email, role, etc.). 

## 4. Group Users
- **List all users in a group**
```http request
GET /api/v1/users/:user_id/groups
```
(You can substitute self for :user_id to get the current user’s groups.) 

## Common Parameters
All of these endpoints support:

per_page / pagination

include[] arrays (e.g. include[]=avatar_url, include[]=enrollments)






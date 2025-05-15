# Table Component

This document outlines how to use the table component in the GradeBench application.

## 1. Overview

The table component provides a standardized way to display tabular data with consistent styling, responsive behavior, and empty state handling.

## 2. Files and Structure

The component consists of one main file:

- `/templates/components/table.html`: Reusable Django template component

## 3. Using the Component in Templates

### 3.1 Basic Usage

Include the table component in your template with the required parameters:

```html
{% include 'components/table.html' with table_id="course-table" headers=headers items=courses responsive=True hover=True %}
    {% block table_body %}
        {% for course in courses %}
            <tr>
                <td>{{ course.name }}</td>
                <td>{{ course.code }}</td>
                <td>{{ course.instructor }}</td>
                <td>
                    <a href="{% url 'course_detail' course.id %}" class="btn btn-sm btn-primary">
                        View
                    </a>
                </td>
            </tr>
        {% endfor %}
    {% endblock %}
```

### 3.2 Content Parameter Alternative

For simpler usage, you can also provide content as a parameter instead of using a block:

```html
{% with table_rows %}
    {% for course in courses %}
        <tr>
            <td>{{ course.name }}</td>
            <td>{{ course.code }}</td>
            <td>{{ course.instructor }}</td>
            <td>
                <a href="{% url 'course_detail' course.id %}" class="btn btn-sm btn-primary">
                    View
                </a>
            </td>
        </tr>
    {% endfor %}
{% endwith %}

{% include 'components/table.html' with 
   table_id="course-table" 
   headers=headers 
   items=courses 
   responsive=True 
   hover=True 
   content=table_rows 
%}
```

### 3.3 Component Parameters

The following parameters can be passed to the component:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| table_id | String | None | Unique identifier for the table |
| table_class | String | None | Additional CSS classes for the table |
| headers | List | None | List of column headers |
| items | List | Required | Data items to display in the table (empty list shows empty state) |
| responsive | Boolean | false | Whether the table should be responsive |
| hover | Boolean | false | Whether to show hover effect on rows |
| striped | Boolean | false | Whether to show striped rows |
| bordered | Boolean | false | Whether to show table borders |
| small | Boolean | false | Whether to use a more compact table |
| header_class | String | text-primary | CSS class for the header row |
| empty_title | String | No data found | Title for empty state |
| empty_message | String | Use the filters... | Message for empty state |
| content | String | None | HTML content for table body (alternative to block) |

## 4. Empty State Handling

The component automatically handles empty data states by displaying a message when the `items` parameter is empty or resolves to false in Django templates.

### 4.1 Default Empty State

By default, when no items are present, the component will display:

```html
<div class="text-center py-5">
    <h3>No data found</h3>
    <p>Use the filters above to change your search criteria or add new items.</p>
</div>
```

### 4.2 Custom Empty State via Parameters

You can customize the empty state message using parameters:

```html
{% include 'components/table.html' with 
   headers=headers 
   items=students 
   empty_title="No students found" 
   empty_message="There are currently no students enrolled in this course." 
%}
```

### 4.3 Custom Empty State via Block

For more complex empty states, you can use the `empty_state` block:

```html
{% include 'components/table.html' with headers=headers items=assignments %}
    {% block table_body %}
        <!-- Table rows -->
    {% endblock %}
    
    {% block empty_state %}
        <h3>No assignments</h3>
        <p>This course has no assignments yet.</p>
        <a href="{% url 'create_assignment' course.id %}" class="btn btn-primary mt-3">
            <i class="fa fa-plus"></i> Create Assignment
        </a>
    {% endblock %}
```

## 5. Examples

### 5.1 Basic Table with Hover Effect

```html
{% include 'components/table.html' with 
   headers=headers 
   items=students 
   hover=True 
   responsive=True 
%}
    {% block table_body %}
        {% for student in students %}
            <tr>
                <td>{{ student.id }}</td>
                <td>{{ student.name }}</td>
                <td>{{ student.email }}</td>
                <td>{{ student.status }}</td>
            </tr>
        {% endfor %}
    {% endblock %}
```

### 5.2 Compact Striped Table

```html
{% include 'components/table.html' with 
   headers=headers 
   items=grades 
   striped=True 
   small=True 
   bordered=True 
%}
    {% block table_body %}
        {% for grade in grades %}
            <tr>
                <td>{{ grade.student.name }}</td>
                <td>{{ grade.assignment.name }}</td>
                <td class="text-end">{{ grade.score }}</td>
                <td class="text-end">{{ grade.possible }}</td>
                <td class="text-end">{{ grade.percentage }}%</td>
            </tr>
        {% endfor %}
    {% endblock %}
```

### 5.3 Table with Custom Header Class

```html
{% include 'components/table.html' with 
   headers=headers 
   items=submissions 
   header_class="bg-dark text-white" 
%}
    {% block table_body %}
        <!-- Table rows -->
    {% endblock %}
```

### 5.4 Table with Actions Column

```html
{% include 'components/table.html' with headers=headers items=courses %}
    {% block table_body %}
        {% for course in courses %}
            <tr>
                <td>{{ course.name }}</td>
                <td>{{ course.code }}</td>
                <td>{{ course.instructor }}</td>
                <td>
                    <div class="btn-group" role="group">
                        <a href="{% url 'view_course' course.id %}" class="btn btn-sm btn-primary">
                            <i class="fa fa-eye"></i>
                        </a>
                        <a href="{% url 'edit_course' course.id %}" class="btn btn-sm btn-secondary">
                            <i class="fa fa-edit"></i>
                        </a>
                        <button class="btn btn-sm btn-danger" data-bs-toggle="modal" 
                                data-bs-target="#delete-modal" data-course-id="{{ course.id }}">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        {% endfor %}
    {% endblock %}
```

## 6. Best Practices

1. **Responsive Design**: Always include the `responsive=True` parameter for tables that may contain a lot of data
2. **Column Widths**: Consider setting explicit widths for columns with short content (like actions)
3. **Row States**: Use Bootstrap contextual classes on rows to indicate status or importance
4. **Pagination**: For large datasets, implement pagination and use the table component for each page
5. **Sorting**: If implementing sortable tables, maintain sort state in the URL for bookmarking
6. **Actions**: Group actions in the last column and use icons with tooltips to save space
7. **Accessibility**: Include proper scope attributes on header cells (`scope="col"`) for screen readers
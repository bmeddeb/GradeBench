# Card Component

This document outlines how to use the card component in the GradeBench application.

## 1. Overview

The card component provides a standardized way to display content in Bootstrap 5 cards with consistent styling and behavior across the application.

## 2. Files and Structure

The component consists of one main file:

- `/templates/components/card.html`: Reusable Django template component

## 3. Using the Component in Templates

### 3.1 Basic Usage

Include the card component in your template with the minimal required parameters:

```html
{% include 'components/card.html' with title="Card Title" %}
    {% block card_content %}
        <p>This is the card content.</p>
    {% endblock %}
```

### 3.2 Content Parameter Alternative

For simpler usage, you can also provide content as a parameter instead of using a block:

```html
{% with card_content="<p>This is the card content.</p>" %}
    {% include 'components/card.html' with title="Card Title" content=card_content %}
{% endwith %}
```

### 3.3 Component Parameters

The following parameters can be passed to the component:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| id | String | None | HTML ID attribute for the card |
| class | String | None | Additional CSS classes for the card |
| title | String | None | Card title displayed in the header |
| subtitle | String | None | Card subtitle/category displayed below the title |
| header_class | String | None | Additional CSS classes for the card header |
| body_class | String | None | Additional CSS classes for the card body |
| content | String | None | HTML content for the card body (alternative to using block) |
| footer | String | None | HTML content for the card footer |
| content_only | Boolean | false | If true, only renders the card content (not the card container) |

## 4. Examples

### 4.1 Basic Card with Title and Subtitle

```html
{% include 'components/card.html' with title="User Profile" subtitle="Personal Information" %}
    {% block card_content %}
        <div class="row">
            <div class="col-md-6">
                <p><strong>Name:</strong> John Doe</p>
                <p><strong>Email:</strong> john.doe@example.com</p>
            </div>
            <div class="col-md-6">
                <p><strong>Role:</strong> Administrator</p>
                <p><strong>Last Login:</strong> Yesterday</p>
            </div>
        </div>
    {% endblock %}
```

### 4.2 Card with Footer

```html
{% include 'components/card.html' with 
   title="Course Details" 
   footer="<a href='#' class='btn btn-primary'>Edit Course</a>" 
%}
    {% block card_content %}
        <p><strong>Course Name:</strong> Introduction to Programming</p>
        <p><strong>Instructor:</strong> Dr. Jane Smith</p>
        <p><strong>Credits:</strong> 3</p>
    {% endblock %}
```

### 4.3 Card with Custom Classes

```html
{% include 'components/card.html' with 
   title="Warning" 
   class="border-warning" 
   header_class="bg-warning text-white"
%}
    {% block card_content %}
        <p>Your account is about to expire. Please renew your subscription.</p>
    {% endblock %}
```

### 4.4 Card with Content Parameter

```html
{% with card_details="<p><strong>Student:</strong> Jane Doe</p><p><strong>ID:</strong> 12345</p>" %}
    {% include 'components/card.html' with 
       title="Student Profile" 
       content=card_details
    %}
{% endwith %}
```

## 5. Best Practices

1. **Consistent Styling**: Use the default card styles when possible for consistent UI
2. **Responsive Content**: Ensure the content inside cards is responsive (using Bootstrap grid)
3. **Content Organization**: Use cards to group related information together
4. **Loading States**: Consider adding `data-loading` attributes for AJAX-loaded card content
5. **Accessibility**: Ensure card content maintains proper heading hierarchy (h1-h6)
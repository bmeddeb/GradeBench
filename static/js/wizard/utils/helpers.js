/**
 * Helper Functions
 * 
 * This module provides utility functions for the wizard.
 */

/**
 * Safely parse JSON string to object
 * @param {string|Object} data - The data to parse
 * @returns {Object|Array} - The parsed data
 */
export function safeParse(data) {
  if (typeof data !== 'string') return data;

  try {
    return JSON.parse(data);
  } catch (e) {
    console.error('Error parsing JSON:', e);
    return [];
  }
}

/**
 * Get a CSRF token from cookies
 * @param {string} name - The name of the cookie
 * @returns {string|null} - The CSRF token or null if not found
 */
export function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Generate a unique ID
 * @returns {string} - A unique ID string
 */
export function generateId() {
  return Math.random().toString(36).substr(2, 9);
}

/**
 * Format a date string
 * @param {string|Date} date - The date to format
 * @param {string} format - The format to use ('short', 'long', etc.)
 * @returns {string} - The formatted date string
 */
export function formatDate(date, format = 'short') {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (format === 'short') {
    return dateObj.toLocaleDateString();
  } else if (format === 'long') {
    return dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString();
  }
  
  return dateObj.toISOString();
}

/**
 * Debounce a function to limit how often it can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - The time to wait in milliseconds
 * @returns {Function} - The debounced function
 */
export function debounce(func, wait = 300) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * Truncate a string if it exceeds a certain length
 * @param {string} str - The string to truncate
 * @param {number} length - The maximum length
 * @returns {string} - The truncated string
 */
export function truncate(str, length = 50) {
  if (!str) return '';
  return str.length > length ? str.substring(0, length) + '...' : str;
}

/**
 * Serialize form data to an object
 * @param {HTMLFormElement} form - The form element
 * @returns {Object} - The serialized form data
 */
export function serializeForm(form) {
  const formData = new FormData(form);
  const data = {};
  
  for (const [key, value] of formData.entries()) {
    // Handle array values
    if (data[key]) {
      if (!Array.isArray(data[key])) {
        data[key] = [data[key]];
      }
      data[key].push(value);
    } else {
      data[key] = value;
    }
  }
  
  return data;
}

/**
 * Create a DOM element with attributes and content
 * @param {string} tag - The HTML tag name
 * @param {Object} attributes - The element attributes
 * @param {string|HTMLElement|Array} content - The element content
 * @returns {HTMLElement} - The created element
 */
export function createElement(tag, attributes = {}, content = '') {
  const element = document.createElement(tag);
  
  // Set attributes
  Object.entries(attributes).forEach(([key, value]) => {
    if (key === 'class' || key === 'className') {
      element.className = value;
    } else if (key === 'style' && typeof value === 'object') {
      Object.assign(element.style, value);
    } else {
      element.setAttribute(key, value);
    }
  });
  
  // Set content
  if (content) {
    if (typeof content === 'string') {
      element.innerHTML = content;
    } else if (content instanceof HTMLElement) {
      element.appendChild(content);
    } else if (Array.isArray(content)) {
      content.forEach(item => {
        if (item instanceof HTMLElement) {
          element.appendChild(item);
        } else if (typeof item === 'string') {
          element.appendChild(document.createTextNode(item));
        }
      });
    }
  }
  
  return element;
}
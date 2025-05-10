// Mermaid loader script - detects if CDN is accessible and falls back to local if needed
(function() {
  // Try to load from CDN first
  function loadMermaidFromCDN() {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10.6.0/dist/mermaid.min.js';
      script.onload = () => {
        console.log('Mermaid loaded from CDN successfully');
        initializeMermaid();
        resolve(true);
      };
      script.onerror = () => {
        console.warn('Failed to load Mermaid from CDN, trying local file');
        reject();
      };
      document.head.appendChild(script);
    });
  }

  // Initialize Mermaid with default settings
  function initializeMermaid() {
    try {
      // Initialize mermaid with configuration
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        logLevel: 'fatal',
        securityLevel: 'loose',
        flowchart: { 
          useMaxWidth: false,
          htmlLabels: true,
          curve: 'basis'
        },
        er: {
          layoutDirection: 'TB',
          entityPadding: 15,
          useMaxWidth: false
        }
      });
    } catch (e) {
      console.error('Failed to initialize Mermaid:', e);
    }
  }

  // Main function to load Mermaid
  function loadMermaid() {
    loadMermaidFromCDN().catch(() => {
      // If CDN fails, notify the user
      const notification = document.createElement('div');
      notification.style.backgroundColor = '#ffecb3';
      notification.style.color = '#333';
      notification.style.padding = '10px';
      notification.style.margin = '10px 0';
      notification.style.borderRadius = '4px';
      notification.style.textAlign = 'center';
      notification.innerHTML = `
        <p><strong>Notice:</strong> Unable to load diagram renderer. 
        Please check your internet connection or use one of these options:</p>
        <p>1. <a href="https://cdn.jsdelivr.net/npm/mermaid@10.6.0/dist/mermaid.min.js" download="mermaid.min.js">
          Download Mermaid</a> and place it in the /js folder</p>
        <p>2. View this documentation online</p>
      `;
      document.body.prepend(notification);
    });
  }

  // Load when the DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadMermaid);
  } else {
    loadMermaid();
  }
})();

#!/bin/bash

# Script to remove CSS and JS files that have been replaced with CDN

echo "Cleaning up CSS libraries..."
rm -f static/css/bootstrap.min.css
rm -f static/css/bootstrap.min.css.map

echo "Cleaning up JS core libraries..."
rm -f static/js/core/jquery.min.js
rm -f static/js/core/popper.min.js
rm -f static/js/core/bootstrap.min.js

echo "Cleaning up JS plugins..."
rm -f static/js/plugins/perfect-scrollbar.jquery.min.js
rm -f static/js/plugins/chartjs.min.js
rm -f static/js/plugins/bootstrap-notify.js

echo "Libraries cleanup complete!"
echo "The following custom files were kept:"
echo "- /static/css/paper-dashboard.css"
echo "- /static/css/paper-dashboard.min.css"
echo "- /static/js/paper-dashboard.min.js"
echo "- /static/js/paper-dashboard.js"
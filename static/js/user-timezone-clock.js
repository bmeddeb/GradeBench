/**
 * Simple clock component to display user's local time
 */

// Requires Luxon: <script src="https://cdn.jsdelivr.net/npm/luxon@3/build/global/luxon.min.js"></script>
document.addEventListener('DOMContentLoaded', function() {
    // Function to update clock
    function updateClock() {
        const clockElement = document.getElementById('user-timezone-clock');
        const dateElement = document.getElementById('user-timezone-date');

        if (clockElement && dateElement && typeof userTimezone !== 'undefined') {
            // Use Luxon to get the time in the user's time zone
            const now = luxon.DateTime.now().setZone(userTimezone);

            // Format time as 12-hour with AM/PM
            const timeString = now.toFormat('hh:mm a');

            // Format date as Month DD, YYYY
            const dateString = now.toFormat('LLL dd, yyyy');

            // Update elements
            clockElement.textContent = timeString;
            dateElement.textContent = dateString;
        }
    }

    // Initial update
    updateClock();

    // Update every second
    setInterval(updateClock, 1000);
});

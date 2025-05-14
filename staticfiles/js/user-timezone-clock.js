/**
 * Simple clock component to display user's local time
 */
document.addEventListener('DOMContentLoaded', function() {
    // Function to update clock
    function updateClock() {
        const clockElement = document.getElementById('user-timezone-clock');
        const dateElement = document.getElementById('user-timezone-date');
        
        if (clockElement && dateElement) {
            const now = new Date();
            
            // Format time as 12-hour format with AM/PM
            let hours = now.getHours();
            const ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            hours = hours ? hours : 12; // Convert 0 to 12 for midnight
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const timeString = `${hours}:${minutes} ${ampm}`;
            
            // Format date compactly as Month DD, YYYY
            const options = { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                timeZone: userTimezone // This variable should be defined in the template
            };
            const dateString = now.toLocaleDateString(undefined, options);
            
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
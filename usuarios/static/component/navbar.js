// Get current page filename
const currentPage = window.parent.location.pathname.split('/').pop();

// Set active state based on current page
document.addEventListener('DOMContentLoaded', function() {
    const navItems = document.querySelectorAll('.navbar span');
    
    navItems.forEach(item => {
        // Remove all active states first
        item.classList.remove('active');
        
        // Set active state for home icon when on home page
        if (item.textContent === 'home' && 
            (currentPage === 'home(mobile).html' || currentPage === '')) {
            item.classList.add('active');
        }
    });
});
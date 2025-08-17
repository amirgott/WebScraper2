// Configuration for the application
const AppConfig = {
    // Base URL for API calls - adjust this based on your environment
    apiBaseUrl: '/api',

    // Full URL for the run_scrape endpoint
    getRunScrapeUrl: function() {
        // For local development with Flask's built-in server
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return window.location.origin + '/run_scrape';
        }

        // For development servers like VS Code's Live Server
        if (window.location.port === '5500' || window.location.port === '63342') {
            // Redirect to the actual Flask server
            return 'http://localhost:5000/run_scrape';
        }

        // Default case - use the current origin with the endpoint path
        return window.location.origin + '/run_scrape';
    }
};

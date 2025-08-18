document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    const scrapeForm = document.getElementById('scrapeForm');
    const freeFormatText = document.getElementById('freeFormatText');
    const runButton = document.getElementById('runButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    const resultContent = document.getElementById('resultContent');

    // Log the elements to make sure they were found
    console.log('Elements found:', {
        scrapeForm: !!scrapeForm,
        freeFormatText: !!freeFormatText,
        runButton: !!runButton
    });

    // Make sure the Run button is initially disabled
    if (runButton) {
        runButton.disabled = true;
        console.log('Run button initially disabled');
    }

    // Function to check if at least one input has data
    function checkInputs() {
        if (!freeFormatText || !runButton) {
            console.error('Missing DOM elements needed for checkInputs');
            return;
        }

        const hasText = freeFormatText.value.trim() !== '';
        const shouldEnable = hasText;
        runButton.disabled = !shouldEnable;

        console.log('Input check - Text:', hasText, 'Button should be enabled:', shouldEnable);

        // Force the button to be enabled if any input has data
        if (shouldEnable && runButton.disabled) {
            console.log('Forcing button to be enabled');
            setTimeout(() => runButton.disabled = false, 0);
        }
    }

    // Event listeners for input changes
    if (freeFormatText) {
        ['input', 'keyup', 'paste', 'change'].forEach(eventType => {
            freeFormatText.addEventListener(eventType, function() {
                console.log(`Text input ${eventType}:`, this.value);
                checkInputs();
            });
        });
    }

    // Form submission
    scrapeForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        resultContainer.classList.add('d-none');
        runButton.disabled = true;

        // Create FormData object
        const formData = new FormData();
        formData.append('free_format_text', freeFormatText.value);

        // Send the request
        let apiUrl;

        // First try to use the config if available
        if (typeof AppConfig !== 'undefined') {
            apiUrl = AppConfig.getRunScrapeUrl();
        } else {
            // Fallback to form action or default
            const formAction = scrapeForm.getAttribute('action') || '/run_scrape';
            apiUrl = formAction.startsWith('http') ? formAction : (window.location.origin + formAction);
        }

        console.log('Submitting to URL:', apiUrl);

        fetch(apiUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            resultContainer.classList.remove('d-none');

            if (data.success) {
                // Show success message
                successMessage.textContent = data.message;
                successMessage.classList.remove('d-none');
                errorMessage.classList.add('d-none');

                // Display results
                displayResults(data.result);

                // Re-enable the run button
                runButton.disabled = false;
            } else {
                // Show error message
                errorMessage.textContent = data.message;
                errorMessage.classList.remove('d-none');
                successMessage.classList.add('d-none');
                resultContent.innerHTML = '';

                // Re-enable the run button
                runButton.disabled = false;
            }
        })
        .catch(error => {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            resultContainer.classList.remove('d-none');

            // Show error message
            errorMessage.textContent = `An error occurred: ${error.message}`;
            errorMessage.classList.remove('d-none');
            successMessage.classList.add('d-none');
            resultContent.innerHTML = '';

            // Re-enable the run button
            runButton.disabled = false;
        });
    });

    // Initial check of inputs
    console.log('Running initial input check...');
    checkInputs();

    // Set a timeout to run the check again after a short delay
    setTimeout(() => {
        console.log('Re-checking inputs after delay...');
        checkInputs();
    }, 500);

    // Function to display results
    function displayResults(result) {
        resultContent.innerHTML = '';

        const resultTable = document.createElement('table');
        resultTable.className = 'table table-striped';

        const tbody = document.createElement('tbody');

        for (const [key, value] of Object.entries(result)) {
            if (value) { // Only show non-empty values
                const row = document.createElement('tr');

                const keyCell = document.createElement('td');
                keyCell.className = 'field-name';
                keyCell.textContent = key;

                const valueCell = document.createElement('td');
                valueCell.className = 'field-value';

                // Special handling for URLs
                if ((key === 'לינק להרשמה' || key === 'לינקים נוספים') && value.startsWith('http')) {
                    const urls = value.split(', ');
                    const linkElements = urls.map(url => {
                        const link = document.createElement('a');
                        link.href = url;
                        link.target = '_blank';
                        link.textContent = url;
                        return link;
                    });

                    linkElements.forEach((link, index) => {
                        valueCell.appendChild(link);
                        if (index < linkElements.length - 1) {
                            valueCell.appendChild(document.createTextNode(', '));
                        }
                    });
                } else {
                    valueCell.textContent = value;
                }

                row.appendChild(keyCell);
                row.appendChild(valueCell);
                tbody.appendChild(row);
            }
        }

        resultTable.appendChild(tbody);
        resultContent.appendChild(resultTable);
    }
});

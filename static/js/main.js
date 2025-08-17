document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    const scrapeForm = document.getElementById('scrapeForm');
    const freeFormatText = document.getElementById('freeFormatText');
    const imageInput = document.getElementById('imageInput');
    const pdfInput = document.getElementById('pdfInput');
    const runButton = document.getElementById('runButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    const resultContent = document.getElementById('resultContent');
    const selectedFile = document.getElementById('selectedFile');
    const imagePlaceholder = document.getElementById('imagePlaceholder');
    const imagePreview = document.getElementById('imagePreview');
    const imageBase64 = document.getElementById('imageBase64');

    // Log the elements to make sure they were found
    console.log('Elements found:', {
        scrapeForm: !!scrapeForm,
        freeFormatText: !!freeFormatText,
        imageInput: !!imageInput,
        pdfInput: !!pdfInput,
        runButton: !!runButton
    });

    // Make sure the Run button is initially disabled
    if (runButton) {
        runButton.disabled = true;
        console.log('Run button initially disabled');
    }

    // Function to check if at least one input has data
    function checkInputs() {
        if (!freeFormatText || !imageInput || !pdfInput || !runButton) {
            console.error('Missing DOM elements needed for checkInputs');
            return;
        }

        const hasText = freeFormatText.value.trim() !== '';
        const hasImage = imageInput.files.length > 0 || (imageBase64 && imageBase64.value !== '');
        const hasPdf = pdfInput.files.length > 0;

        const shouldEnable = hasText || hasImage || hasPdf;
        runButton.disabled = !shouldEnable;

        console.log('Input check - Text:', hasText, 'Image:', hasImage, 'PDF:', hasPdf, 'Button should be enabled:', shouldEnable);

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

    if (imageInput) {
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.classList.remove('d-none');
                    imagePlaceholder.classList.add('d-none');
                    imageBase64.value = e.target.result;
                };
                reader.readAsDataURL(this.files[0]);
            }
            checkInputs();
        });
    }

    // Handle paste events for the image placeholder
    document.addEventListener('paste', function(e) {
        if (e.clipboardData && e.clipboardData.items) {
            const items = e.clipboardData.items;
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const blob = items[i].getAsFile();
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        imagePreview.src = e.target.result;
                        imagePreview.classList.remove('d-none');
                        imagePlaceholder.classList.add('d-none');
                        imageBase64.value = e.target.result;
                        checkInputs();
                    };
                    reader.readAsDataURL(blob);
                    break;
                }
            }
        }
    });

    // Handle drag and drop for the image placeholder
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        imagePlaceholder.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        imagePlaceholder.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        imagePlaceholder.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        imagePlaceholder.style.backgroundColor = '#e9ecef';
    }

    function unhighlight() {
        imagePlaceholder.style.backgroundColor = '';
    }

    imagePlaceholder.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files[0]) {
            const file = files[0];
            if (file.type.indexOf('image') !== -1) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.classList.remove('d-none');
                    imagePlaceholder.classList.add('d-none');
                    imageBase64.value = e.target.result;
                    checkInputs();
                };
                reader.readAsDataURL(file);
            }
        }
    });

    // Click on placeholder to trigger file input
    imagePlaceholder.addEventListener('click', function() {
        imageInput.click();
    });

    // Show selected PDF filename
    pdfInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            selectedFile.textContent = `Selected file: ${this.files[0].name}`;
        } else {
            selectedFile.textContent = '';
        }
        checkInputs();
    });

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

        if (imageInput.files.length > 0) {
            formData.append('image', imageInput.files[0]);
        } else if (imageBase64.value) {
            formData.append('image_base64', imageBase64.value);
        }

        if (pdfInput.files.length > 0) {
            formData.append('pdf_file', pdfInput.files[0]);
        }

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

                // Special handling for URLs and images
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
                } else if (key === 'IMAGE' && value.startsWith('http')) {
                    const img = document.createElement('img');
                    img.src = value;
                    img.className = 'img-fluid';
                    img.style.maxHeight = '100px';
                    valueCell.appendChild(img);
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

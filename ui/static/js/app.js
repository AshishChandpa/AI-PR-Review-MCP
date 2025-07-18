document.addEventListener('DOMContentLoaded', function() {
    const reviewForm = document.getElementById('reviewForm');
    const providerSelect = document.getElementById('provider');
    const modelSelect = document.getElementById('model');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const reviewResult = document.getElementById('reviewResult');
    const reviewContent = document.getElementById('reviewContent');

    // Provider data
    let providers = {};

    // Load providers on page load
    loadProviders();

    // Update models when provider changes
    providerSelect.addEventListener('change', function() {
        updateModels();
    });

    // Handle form submission
    reviewForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(reviewForm);

        // Show loading state
        loadingSpinner.classList.remove('d-none');
        reviewResult.style.display = 'none';

        try {
            const response = await fetch('/api/review', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayReview(result);
            } else {
                showError(result.error);
            }
        } catch (error) {
            showError('Failed to review PR: ' + error.message);
        } finally {
            loadingSpinner.classList.add('d-none');
        }
    });

    async function loadProviders() {
        try {
            const response = await fetch('/api/providers');
            providers = await response.json();
            updateModels();
        } catch (error) {
            console.error('Failed to load providers:', error);
        }
    }

    function updateModels() {
        const selectedProvider = providerSelect.value;
        const providerInfo = providers[selectedProvider];

        modelSelect.innerHTML = '<option value="">Auto (Default)</option>';

        if (providerInfo && providerInfo.models) {
            providerInfo.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === providerInfo.default_model) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
        }
    }

    function displayReview(result) {
        const html = `
            <div class="review-header mb-3">
                <h6>PR: ${result.pr_info.title}</h6>
                <div class="d-flex justify-content-between text-muted small">
                    <span>Files changed: ${result.pr_info.files_changed}</span>
                    <span>+${result.pr_info.additions} -${result.pr_info.deletions}</span>
                    <span>Provider: ${result.provider}</span>
                    <span>Model: ${result.model}</span>
                </div>
            </div>
            <div class="review-content">
                <pre class="bg-light p-3 rounded">${result.review}</pre>
            </div>
        `;

        reviewContent.innerHTML = html;
        reviewResult.style.display = 'block';
    }

    function showError(message) {
        reviewContent.innerHTML = `
            <div class="alert alert-danger" role="alert">
                ${message}
            </div>
        `;
        reviewResult.style.display = 'block';
    }
});

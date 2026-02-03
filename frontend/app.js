/**
 * Lumina Photo Enhancer - Frontend Application
 */

// API Configuration
// Change this to your Render backend URL after deployment
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-render-app.onrender.com';  // UPDATE THIS after Render deployment

// State
let currentJobId = null;
let wsConnection = null;

// DOM Elements
const elements = {
    // Connect
    storeUrl: document.getElementById('store-url'),
    accessToken: document.getElementById('access-token'),
    connectBtn: document.getElementById('connect-btn'),
    connectError: document.getElementById('connect-error'),

    // Sections
    connectSection: document.getElementById('connect-section'),
    storeSection: document.getElementById('store-section'),
    productsSection: document.getElementById('products-section'),
    enhanceSection: document.getElementById('enhance-section'),
    progressSection: document.getElementById('progress-section'),
    resultsSection: document.getElementById('results-section'),

    // Store info
    shopName: document.getElementById('shop-name'),
    shopDomain: document.getElementById('shop-domain'),
    productCount: document.getElementById('product-count'),
    toEnhanceCount: document.getElementById('to-enhance-count'),

    // Products
    productsGrid: document.getElementById('products-grid'),
    productsLoading: document.getElementById('products-loading'),
    refreshProducts: document.getElementById('refresh-products'),

    // Enhancement
    skipEnhanced: document.getElementById('skip-enhanced'),
    deleteOld: document.getElementById('delete-old'),
    maxProducts: document.getElementById('max-products'),
    startBtn: document.getElementById('start-btn'),

    // Progress
    progressStatus: document.getElementById('progress-status'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    progressCount: document.getElementById('progress-count'),
    currentProductTitle: document.getElementById('current-product-title'),
    etaText: document.getElementById('eta-text'),
    stopBtn: document.getElementById('stop-btn'),

    // Results
    resultsStatus: document.getElementById('results-status'),
    resultSuccess: document.getElementById('result-success'),
    resultFailed: document.getElementById('result-failed'),
    resultImages: document.getElementById('result-images'),
    resultTime: document.getElementById('result-time'),
    restartBtn: document.getElementById('restart-btn')
};

// Store credentials
let storeCredentials = {
    storeUrl: '',
    accessToken: ''
};

// ============================================
// API Functions
// ============================================

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

// ============================================
// Connect Store
// ============================================

async function connectStore() {
    const storeUrl = elements.storeUrl.value.trim();
    const accessToken = elements.accessToken.value.trim();

    if (!storeUrl || !accessToken) {
        showError('Please enter both store URL and access token');
        return;
    }

    // Show loading
    elements.connectBtn.disabled = true;
    elements.connectBtn.querySelector('.btn-text').textContent = 'Connecting...';
    hideError();

    try {
        const result = await apiCall('/api/connect', 'POST', {
            store_url: storeUrl,
            access_token: accessToken
        });

        if (result.success) {
            // Store credentials
            storeCredentials = { storeUrl, accessToken };

            // Update UI
            elements.shopName.textContent = result.shop_name || 'Unknown';
            elements.shopDomain.textContent = result.shop_domain || storeUrl;
            elements.productCount.textContent = result.product_count || 0;

            // Show next sections
            elements.storeSection.classList.remove('hidden');
            elements.productsSection.classList.remove('hidden');
            elements.enhanceSection.classList.remove('hidden');

            // Hide connect form
            elements.connectSection.querySelector('.card-body').style.display = 'none';

            // Load products
            await loadProducts();
        } else {
            showError(result.error || 'Failed to connect');
        }
    } catch (error) {
        showError(`Connection failed: ${error.message}`);
    } finally {
        elements.connectBtn.disabled = false;
        elements.connectBtn.querySelector('.btn-text').textContent = 'Connect Store';
    }
}

// ============================================
// Load Products
// ============================================

async function loadProducts() {
    elements.productsLoading.classList.remove('hidden');
    elements.productsGrid.innerHTML = '';

    try {
        const result = await apiCall('/api/products', 'POST', {
            store_url: storeCredentials.storeUrl,
            access_token: storeCredentials.accessToken
        });

        if (result.success) {
            // Count to enhance (without AI tag)
            const toEnhance = result.products.filter(p => !p.has_ai_tag).length;
            elements.toEnhanceCount.textContent = toEnhance;

            // Render products
            renderProducts(result.products);
        }
    } catch (error) {
        console.error('Failed to load products:', error);
        elements.productsGrid.innerHTML = `<p class="error-message">Failed to load products: ${error.message}</p>`;
    } finally {
        elements.productsLoading.classList.add('hidden');
    }
}

function renderProducts(products) {
    elements.productsGrid.innerHTML = products.slice(0, 50).map(product => `
        <div class="product-card">
            <img src="${product.first_image || 'https://via.placeholder.com/150?text=No+Image'}" 
                 alt="${product.title}"
                 onerror="this.src='https://via.placeholder.com/150?text=No+Image'">
            ${product.has_ai_tag ? '<span class="ai-badge">AI Enhanced</span>' : ''}
            <div class="product-title">${product.title}</div>
        </div>
    `).join('');
}

// ============================================
// Start Enhancement
// ============================================

async function startEnhancement() {
    const maxProducts = elements.maxProducts.value ? parseInt(elements.maxProducts.value) : null;
    const skipAiEnhanced = elements.skipEnhanced.checked;
    const deleteOldImages = elements.deleteOld.checked;

    elements.startBtn.disabled = true;

    try {
        const result = await apiCall('/api/enhance', 'POST', {
            store_url: storeCredentials.storeUrl,
            access_token: storeCredentials.accessToken,
            max_products: maxProducts,
            skip_ai_enhanced: skipAiEnhanced,
            delete_old_images: deleteOldImages
        });

        currentJobId = result.job_id;

        // Show progress section
        elements.enhanceSection.classList.add('hidden');
        elements.progressSection.classList.remove('hidden');

        // Start polling for progress
        pollJobStatus();

        // Try WebSocket connection
        connectWebSocket();

    } catch (error) {
        alert(`Failed to start enhancement: ${error.message}`);
        elements.startBtn.disabled = false;
    }
}

// ============================================
// Progress Tracking
// ============================================

async function pollJobStatus() {
    if (!currentJobId) return;

    try {
        const status = await apiCall(`/api/status/${currentJobId}`);
        updateProgress(status);

        if (status.status === 'running' || status.status === 'pending') {
            setTimeout(pollJobStatus, 2000);
        } else if (status.status === 'completed') {
            showResults(status.result);
        } else if (status.status === 'failed') {
            showError(status.error || 'Enhancement failed');
            resetToStart();
        }
    } catch (error) {
        console.error('Failed to get job status:', error);
        setTimeout(pollJobStatus, 5000);
    }
}

function connectWebSocket() {
    if (!currentJobId) return;

    const wsUrl = API_BASE_URL.replace('http', 'ws') + `/ws/progress/${currentJobId}`;

    try {
        wsConnection = new WebSocket(wsUrl);

        wsConnection.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateProgress(data);
        };

        wsConnection.onerror = (error) => {
            console.log('WebSocket error, falling back to polling');
        };
    } catch (error) {
        console.log('WebSocket not available, using polling');
    }
}

function updateProgress(data) {
    // Update progress bar
    const percent = data.progress || 0;
    elements.progressFill.style.width = `${percent}%`;
    elements.progressText.textContent = `${percent}%`;

    // Update counts
    elements.progressCount.textContent = `${data.current_product || 0} / ${data.total_products || 0} products`;

    // Update current product
    elements.currentProductTitle.textContent = data.current_product_title || '-';

    // Update ETA
    if (data.eta_seconds) {
        const minutes = Math.ceil(data.eta_seconds / 60);
        elements.etaText.textContent = `~${minutes} minutes remaining`;
    }

    // Update status badge
    elements.progressStatus.textContent = data.status === 'running' ? 'Running' : data.status;
}

async function stopEnhancement() {
    if (!currentJobId) return;

    try {
        await apiCall(`/api/stop/${currentJobId}`, 'POST');
        elements.progressStatus.textContent = 'Stopping...';
    } catch (error) {
        console.error('Failed to stop:', error);
    }
}

// ============================================
// Results
// ============================================

function showResults(result) {
    // Close WebSocket
    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }

    // Hide progress, show results
    elements.progressSection.classList.add('hidden');
    elements.resultsSection.classList.remove('hidden');

    // Update results
    elements.resultSuccess.textContent = result.successful_products || 0;
    elements.resultFailed.textContent = result.failed_products || 0;
    elements.resultImages.textContent = result.enhanced_images || 0;
    elements.resultTime.textContent = Math.round((result.total_minutes || 0) * 10) / 10;

    // Update status
    if (result.failed_products > 0) {
        elements.resultsStatus.classList.remove('success');
        elements.resultsStatus.classList.add('warning');
        elements.resultsStatus.textContent = 'Partial';
    }
}

function resetToStart() {
    currentJobId = null;

    // Hide all sections except connect
    elements.progressSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    elements.enhanceSection.classList.remove('hidden');

    // Re-enable start button
    elements.startBtn.disabled = false;
}

// ============================================
// Utilities
// ============================================

function showError(message) {
    elements.connectError.textContent = message;
    elements.connectError.classList.remove('hidden');
}

function hideError() {
    elements.connectError.classList.add('hidden');
}

// ============================================
// Event Listeners
// ============================================

elements.connectBtn.addEventListener('click', connectStore);
elements.refreshProducts.addEventListener('click', loadProducts);
elements.startBtn.addEventListener('click', startEnhancement);
elements.stopBtn.addEventListener('click', stopEnhancement);
elements.restartBtn.addEventListener('click', () => {
    resetToStart();
    loadProducts();
});

// Enter key on inputs
elements.storeUrl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') elements.accessToken.focus();
});
elements.accessToken.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') connectStore();
});

// ============================================
// Initialize
// ============================================

console.log('Lumina Photo Enhancer initialized');
console.log(`API URL: ${API_BASE_URL}`);

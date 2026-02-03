"""
FastAPI Server for Photo Enhancement System.

Provides REST API endpoints for:
- Shopify store connection
- Product listing
- Enhancement job management
- Progress tracking via WebSocket

Deployment: Render (backend) + Vercel (frontend)
"""

import os
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from photo_enhancer import PhotoEnhancer, EnhancementResult
from shopify_graphql import ShopifyGraphQLClient
from parallel_gemini import load_api_keys_from_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server")


# ============================================
# Data Models
# ============================================

class ConnectRequest(BaseModel):
    store_url: str
    access_token: str


class ConnectResponse(BaseModel):
    success: bool
    shop_name: Optional[str] = None
    shop_domain: Optional[str] = None
    product_count: Optional[int] = None
    error: Optional[str] = None


class EnhanceRequest(BaseModel):
    store_url: str
    access_token: str
    max_products: Optional[int] = None
    skip_ai_enhanced: bool = True
    delete_old_images: bool = True


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    current_product: int
    total_products: int
    current_product_title: Optional[str] = None
    start_time: Optional[str] = None
    eta_seconds: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


# ============================================
# Global State
# ============================================

# Active jobs
active_jobs: Dict[str, JobStatus] = {}
job_results: Dict[str, EnhancementResult] = {}

# WebSocket connections for progress updates
ws_connections: Dict[str, List[WebSocket]] = {}

# Gemini API keys (loaded from env)
gemini_keys: List[str] = []


# ============================================
# Lifespan
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load API keys on startup."""
    global gemini_keys
    gemini_keys = load_api_keys_from_env()
    
    if gemini_keys:
        logger.info(f"✅ Loaded {len(gemini_keys)} Gemini API keys")
    else:
        logger.warning("⚠️ No Gemini API keys found! Set GEMINI_API_KEY_1, etc.")
    
    yield
    
    # Cleanup
    logger.info("Server shutting down")


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Lumina Photo Enhancer API",
    description="AI-powered Shopify product image enhancement",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Serve Frontend (Single Page App)
# ============================================

FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lumina Photo Enhancer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a28;
            --accent: #6366f1;
            --accent-light: #818cf8;
            --accent-glow: rgba(99, 102, 241, 0.25);
            --success: #10b981;
            --error: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: #2d2d4a;
            --gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }
        .container { max-width: 960px; margin: 0 auto; padding: 2rem; }
        
        /* Header */
        .header { text-align: center; margin-bottom: 2.5rem; }
        .logo { display: flex; align-items: center; justify-content: center; gap: 0.75rem; margin-bottom: 0.5rem; }
        .logo-icon { font-size: 2.5rem; }
        .logo h1 {
            font-size: 2rem;
            font-weight: 700;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .tagline { color: var(--text-secondary); font-size: 1rem; }
        .key-status {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success);
            border-radius: 20px;
            color: var(--success);
            font-size: 0.875rem;
        }
        .key-status.warning {
            background: rgba(239, 68, 68, 0.1);
            border-color: var(--error);
            color: var(--error);
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            margin-bottom: 1.5rem;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .card:hover { border-color: var(--accent); box-shadow: 0 0 30px var(--accent-glow); }
        .card-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
            background: rgba(255,255,255,0.02);
        }
        .card-header h2 { font-size: 1.125rem; font-weight: 600; flex: 1; }
        .card-body { padding: 1.5rem; }
        
        /* Step Badge */
        .step-badge {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: var(--gradient);
            color: white;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.875rem; font-weight: 700;
        }
        .step-badge.success { background: var(--success); }
        
        /* Forms */
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group.full { grid-column: 1 / -1; }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
        }
        .form-group input {
            width: 100%;
            padding: 0.875rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.2s;
        }
        .form-group input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        .form-group input::placeholder { color: var(--text-muted); }
        .form-group small { display: block; margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted); }
        
        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.875rem 1.75rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: var(--gradient);
            color: white;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px var(--accent-glow); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-danger { background: var(--error); color: white; }
        .btn-small { padding: 0.5rem 1rem; font-size: 0.875rem; background: var(--bg-secondary); color: var(--text-secondary); border: 1px solid var(--border); cursor: pointer; }
        .btn-small:hover { border-color: var(--accent); color: var(--text-primary); }
        .btn-small.active { background: var(--accent); color: white; border-color: var(--accent); }
        .btn-large { width: 100%; padding: 1rem; font-size: 1.125rem; }
        
        /* Store Info */
        .store-info { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
        .info-item { background: var(--bg-secondary); padding: 1rem; border-radius: 10px; text-align: center; }
        .info-item .label { display: block; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem; }
        .info-item .value { font-size: 1.25rem; font-weight: 700; }
        .info-item .value.success { color: var(--success); }
        
        /* Products Grid */
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 1rem;
            max-height: 350px;
            overflow-y: auto;
        }
        .product-card {
            background: var(--bg-secondary);
            border-radius: 10px;
            overflow: hidden;
            transition: all 0.2s;
            position: relative;
        }
        .product-card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
        .product-card img { width: 100%; height: 120px; object-fit: cover; }
        .product-card .title { padding: 0.75rem; font-size: 0.75rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .product-card .ai-badge {
            position: absolute;
            top: 0.5rem; right: 0.5rem;
            padding: 0.25rem 0.5rem;
            background: var(--success);
            border-radius: 4px;
            font-size: 0.625rem;
            font-weight: 700;
        }
        
        /* Options */
        .options { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
        .option label { display: flex; align-items: center; gap: 0.75rem; color: var(--text-secondary); cursor: pointer; font-size: 0.875rem; }
        .option input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); }
        .option input[type="number"] { width: 80px; padding: 0.5rem; margin-left: 0.5rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; color: var(--text-primary); }
        
        /* Progress */
        .progress-bar { width: 100%; height: 16px; background: var(--bg-secondary); border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
        .progress-fill { height: 100%; background: var(--gradient); border-radius: 8px; transition: width 0.3s ease; }
        .progress-stats { display: flex; justify-content: space-between; margin-bottom: 1rem; font-size: 0.875rem; color: var(--text-secondary); }
        .progress-stats .percent { font-size: 1.5rem; font-weight: 700; color: var(--accent-light); }
        .current-info { padding: 1rem; background: var(--bg-secondary); border-radius: 10px; margin-bottom: 1rem; }
        .current-info .label { color: var(--text-muted); font-size: 0.75rem; }
        .current-info .value { font-weight: 600; }
        
        /* Results */
        .results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
        .result-item { text-align: center; padding: 1.25rem; background: var(--bg-secondary); border-radius: 10px; }
        .result-item .number { display: block; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.25rem; }
        .result-item.success .number { color: var(--success); }
        .result-item.error .number { color: var(--error); }
        .result-item .label { font-size: 0.75rem; color: var(--text-muted); }
        
        /* Error */
        .error-msg { margin-top: 1rem; padding: 1rem; background: rgba(239,68,68,0.1); border: 1px solid var(--error); border-radius: 10px; color: var(--error); font-size: 0.875rem; }
        
        /* Utilities */
        .hidden { display: none !important; }
        .loading { text-align: center; padding: 2rem; color: var(--text-muted); }
        
        /* Responsive */
        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .store-info, .results-grid { grid-template-columns: repeat(2, 1fr); }
            .options { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="logo">
                <span class="logo-icon">✨</span>
                <h1>Lumina Photo Enhancer</h1>
            </div>
            <p class="tagline">AI-Powered Shopify Product Image Enhancement</p>
            <div id="key-status" class="key-status">Loading...</div>
        </header>

        <!-- Step 1: Connect -->
        <section id="connect-section" class="card">
            <div class="card-header">
                <span class="step-badge">1</span>
                <h2>Connect Your Shopify Store</h2>
            </div>
            <div class="card-body">
                <div class="form-row">
                    <div class="form-group">
                        <label>Store URL</label>
                        <input type="text" id="store-url" placeholder="your-store.myshopify.com" />
                    </div>
                    <div class="form-group">
                        <label>Access Token</label>
                        <input type="password" id="access-token" placeholder="shpat_xxxxxxxxxxxx" />
                    </div>
                </div>
                <button id="connect-btn" class="btn btn-primary">
                    🔗 Connect Store
                </button>
                <div id="connect-error" class="error-msg hidden"></div>
            </div>
        </section>

        <!-- Store Info (hidden initially) -->
        <section id="store-section" class="card hidden">
            <div class="card-header">
                <span class="step-badge success">✓</span>
                <h2>Store Connected</h2>
            </div>
            <div class="card-body">
                <div class="store-info">
                    <div class="info-item">
                        <span class="label">Store</span>
                        <span id="shop-name" class="value">-</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Domain</span>
                        <span id="shop-domain" class="value">-</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Products</span>
                        <span id="product-count" class="value">-</span>
                    </div>
                    <div class="info-item">
                        <span class="label">To Enhance</span>
                        <span id="to-enhance" class="value success">-</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Products Preview -->
        <section id="products-section" class="card hidden">
            <div class="card-header">
                <span class="step-badge">2</span>
                <h2>Products Preview</h2>
                <button id="refresh-btn" class="btn btn-small">↻ Refresh</button>
            </div>
            <div class="card-body">
                <div id="products-grid" class="products-grid"></div>
                <div id="products-loading" class="loading hidden">Loading products...</div>
            </div>
        </section>

        <!-- Start Enhancement -->
        <section id="enhance-section" class="card hidden">
            <div class="card-header">
                <span class="step-badge">3</span>
                <h2>Start Enhancement</h2>
            </div>
            <div class="card-body">
                <div class="options">
                    <div class="option">
                        <label><input type="checkbox" id="skip-enhanced" checked /> Skip already enhanced</label>
                    </div>
                    <div class="option">
                        <label><input type="checkbox" id="delete-old" checked /> Replace original images</label>
                    </div>
                </div>
                
                <!-- Quick Test Presets -->
                <div style="margin-bottom: 1.5rem;">
                    <label style="display: block; margin-bottom: 0.75rem; font-size: 0.875rem; color: var(--text-secondary);">Select how many products to enhance:</label>
                    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                        <button class="btn btn-small preset-btn" data-count="10">10 Products</button>
                        <button class="btn btn-small preset-btn" data-count="20">20 Products</button>
                        <button class="btn btn-small preset-btn" data-count="30">30 Products</button>
                        <button class="btn btn-small preset-btn" data-count="50">50 Products</button>
                        <button class="btn btn-small preset-btn" data-count="100">100 Products</button>
                        <button class="btn btn-small preset-btn active" data-count="">All Products</button>
                    </div>
                    <input type="hidden" id="max-products" value="" />
                </div>
                
                <button id="start-btn" class="btn btn-primary btn-large">
                    🚀 Start Enhancement
                </button>
            </div>
        </section>

        <!-- Progress -->
        <section id="progress-section" class="card hidden">
            <div class="card-header">
                <span class="step-badge">⚡</span>
                <h2>Enhancement in Progress</h2>
            </div>
            <div class="card-body">
                <div class="progress-bar">
                    <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-stats">
                    <span id="progress-percent" class="percent">0%</span>
                    <span id="progress-count">0 / 0 products</span>
                </div>
                <div class="current-info">
                    <div class="label">Current Product</div>
                    <div id="current-product" class="value">-</div>
                </div>
                <div class="current-info">
                    <div class="label">Estimated Time Remaining</div>
                    <div id="eta" class="value">Calculating...</div>
                </div>
                <button id="stop-btn" class="btn btn-danger btn-large">⏹ Stop Enhancement</button>
            </div>
        </section>

        <!-- Results -->
        <section id="results-section" class="card hidden">
            <div class="card-header">
                <span class="step-badge success">✓</span>
                <h2>Enhancement Complete</h2>
            </div>
            <div class="card-body">
                <div class="results-grid">
                    <div class="result-item success">
                        <span id="result-success" class="number">0</span>
                        <span class="label">Successful</span>
                    </div>
                    <div class="result-item error">
                        <span id="result-failed" class="number">0</span>
                        <span class="label">Failed</span>
                    </div>
                    <div class="result-item">
                        <span id="result-images" class="number">0</span>
                        <span class="label">Images</span>
                    </div>
                    <div class="result-item">
                        <span id="result-time" class="number">0</span>
                        <span class="label">Minutes</span>
                    </div>
                </div>
                
                <!-- Enhanced Products List -->
                <div id="enhanced-products-section" class="hidden" style="margin-top: 1.5rem;">
                    <h3 style="font-size: 1rem; margin-bottom: 1rem; color: var(--text-secondary);">✅ Enhanced Products:</h3>
                    <div id="enhanced-products-list" style="max-height: 250px; overflow-y: auto; background: var(--bg-secondary); border-radius: 10px; padding: 1rem;"></div>
                </div>
                
                <button id="restart-btn" class="btn btn-primary btn-large" style="margin-top: 1.5rem;">↻ Start New Enhancement</button>
            </div>
        </section>
    </div>

    <script>
        const API = '';  // Same origin
        let credentials = { storeUrl: '', accessToken: '' };
        let currentJobId = null;
        
        // Elements
        const $ = id => document.getElementById(id);
        
        // Check API keys on load
        async function checkKeys() {
            try {
                const res = await fetch(API + '/api/keys');
                const data = await res.json();
                const el = $('key-status');
                if (data.loaded > 0) {
                    el.textContent = `✓ ${data.loaded} Gemini API Keys Loaded`;
                    el.classList.remove('warning');
                } else {
                    el.textContent = '✗ No Gemini API Keys - Add them to .env';
                    el.classList.add('warning');
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        // Connect store
        async function connect() {
            const storeUrl = $('store-url').value.trim();
            const accessToken = $('access-token').value.trim();
            
            if (!storeUrl || !accessToken) {
                showError('connect-error', 'Please enter both store URL and access token');
                return;
            }
            
            $('connect-btn').disabled = true;
            $('connect-btn').textContent = 'Connecting...';
            hideError('connect-error');
            
            try {
                const res = await fetch(API + '/api/connect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ store_url: storeUrl, access_token: accessToken })
                });
                const data = await res.json();
                
                if (data.success) {
                    credentials = { storeUrl, accessToken };
                    $('shop-name').textContent = data.shop_name || 'Unknown';
                    $('shop-domain').textContent = data.shop_domain || storeUrl;
                    $('product-count').textContent = data.product_count || 0;
                    $('to-enhance').textContent = data.product_count || 0;
                    
                    $('store-section').classList.remove('hidden');
                    $('enhance-section').classList.remove('hidden');
                    $('connect-section').querySelector('.card-body').style.display = 'none';
                    
                    // Products will be fetched when enhancement starts (no duplicate fetch)
                } else {
                    showError('connect-error', data.error || 'Connection failed');
                }
            } catch (e) {
                showError('connect-error', 'Error: ' + e.message);
            } finally {
                $('connect-btn').disabled = false;
                $('connect-btn').textContent = '🔗 Connect Store';
            }
        }
        
        // Load products
        async function loadProducts() {
            $('products-loading').classList.remove('hidden');
            $('products-grid').innerHTML = '';
            
            try {
                const res = await fetch(API + '/api/products', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ store_url: credentials.storeUrl, access_token: credentials.accessToken })
                });
                const data = await res.json();
                
                if (data.success) {
                    const toEnhance = data.products.filter(p => !p.has_ai_tag).length;
                    $('to-enhance').textContent = toEnhance;
                    
                    $('products-grid').innerHTML = data.products.slice(0, 50).map(p => `
                        <div class="product-card">
                            <img src="${p.first_image || 'https://via.placeholder.com/150?text=No+Image'}" 
                                 onerror="this.src='https://via.placeholder.com/150?text=No+Image'" alt="">
                            ${p.has_ai_tag ? '<span class="ai-badge">AI</span>' : ''}
                            <div class="title">${p.title}</div>
                        </div>
                    `).join('');
                }
            } catch (e) {
                $('products-grid').innerHTML = '<p class="error-msg">Failed to load: ' + e.message + '</p>';
            } finally {
                $('products-loading').classList.add('hidden');
            }
        }
        
        // Start enhancement
        async function startEnhancement() {
            $('start-btn').disabled = true;
            
            try {
                const res = await fetch(API + '/api/enhance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        store_url: credentials.storeUrl,
                        access_token: credentials.accessToken,
                        max_products: $('max-products').value ? parseInt($('max-products').value) : null,
                        skip_ai_enhanced: $('skip-enhanced').checked,
                        delete_old_images: $('delete-old').checked
                    })
                });
                const data = await res.json();
                
                currentJobId = data.job_id;
                $('enhance-section').classList.add('hidden');
                $('progress-section').classList.remove('hidden');
                
                pollProgress();
            } catch (e) {
                alert('Error: ' + e.message);
                $('start-btn').disabled = false;
            }
        }
        
        // Poll progress
        async function pollProgress() {
            if (!currentJobId) return;
            
            try {
                const res = await fetch(API + '/api/status/' + currentJobId);
                
                // Stop polling if job not found (server restarted)
                if (res.status === 404) {
                    console.log('Job not found, stopping poll');
                    currentJobId = null;
                    resetUI();
                    return;
                }
                
                const data = await res.json();
                
                $('progress-fill').style.width = data.progress + '%';
                $('progress-percent').textContent = data.progress + '%';
                $('progress-count').textContent = `${data.current_product} / ${data.total_products} products`;
                $('current-product').textContent = data.current_product_title || '-';
                
                if (data.eta_seconds) {
                    const mins = Math.ceil(data.eta_seconds / 60);
                    $('eta').textContent = `~${mins} minute${mins !== 1 ? 's' : ''}`;
                }
                
                if (data.status === 'completed') {
                    showResults(data.result);
                } else if (data.status === 'failed') {
                    alert('Enhancement failed: ' + data.error);
                    resetUI();
                } else {
                    setTimeout(pollProgress, 2000);
                }
            } catch (e) {
                console.error('Poll error:', e);
                // Stop polling on errors
                currentJobId = null;
                resetUI();
            }
        }
        
        // Stop enhancement
        async function stopEnhancement() {
            if (!currentJobId) return;
            try {
                await fetch(API + '/api/stop/' + currentJobId, { method: 'POST' });
                $('stop-btn').textContent = 'Stopping...';
            } catch (e) {
                console.error(e);
            }
        }
        
        // Show results
        function showResults(result) {
            $('progress-section').classList.add('hidden');
            $('results-section').classList.remove('hidden');
            
            $('result-success').textContent = result.successful_products || 0;
            $('result-failed').textContent = result.failed_products || 0;
            $('result-images').textContent = result.enhanced_images || 0;
            $('result-time').textContent = Math.round((result.total_minutes || 0) * 10) / 10;
            
            // Show enhanced product names if available
            const productNames = result.successful_product_names || [];
            if (productNames.length > 0) {
                $('enhanced-products-section').classList.remove('hidden');
                $('enhanced-products-list').innerHTML = productNames.map((name, i) => 
                    `<div style="padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-size: 0.875rem;">
                        <span style="color: var(--success); margin-right: 0.5rem;">✓</span>
                        ${name}
                    </div>`
                ).join('');
            } else {
                $('enhanced-products-section').classList.add('hidden');
            }
        }
        
        // Reset UI
        function resetUI() {
            currentJobId = null;
            $('progress-section').classList.add('hidden');
            $('results-section').classList.add('hidden');
            $('enhance-section').classList.remove('hidden');
            $('start-btn').disabled = false;
            $('stop-btn').textContent = '⏹ Stop Enhancement';
            loadProducts();
        }
        
        // Helpers
        function showError(id, msg) { const el = $(id); el.textContent = msg; el.classList.remove('hidden'); }
        function hideError(id) { $(id).classList.add('hidden'); }
        
        // Event listeners
        $('connect-btn').addEventListener('click', connect);
        $('refresh-btn').addEventListener('click', loadProducts);
        $('start-btn').addEventListener('click', startEnhancement);
        $('stop-btn').addEventListener('click', stopEnhancement);
        $('restart-btn').addEventListener('click', resetUI);
        
        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                $('max-products').value = btn.dataset.count;
            });
        });
        
        // Enter key
        $('store-url').addEventListener('keypress', e => { if (e.key === 'Enter') $('access-token').focus(); });
        $('access-token').addEventListener('keypress', e => { if (e.key === 'Enter') connect(); });
        
        // Init
        checkKeys();
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_root():
    """Serve the frontend."""
    return FRONTEND_HTML


@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    """Serve the frontend (alias)."""
    return FRONTEND_HTML


# ============================================
# API Endpoints
# ============================================

@app.get("/api/health")
async def health():
    """Health check for Render."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/keys")
async def get_keys_status():
    """Get status of loaded Gemini API keys."""
    return {
        "loaded": len(gemini_keys),
        "keys": [f"{k[:8]}..." for k in gemini_keys]
    }


@app.post("/api/connect", response_model=ConnectResponse)
async def connect_store(request: ConnectRequest):
    """Validate Shopify store connection."""
    try:
        client = ShopifyGraphQLClient(request.store_url, request.access_token)
        shop = await client.validate_connection()
        count = await client.get_products_count()
        
        return ConnectResponse(
            success=True,
            shop_name=shop.get("name"),
            shop_domain=shop.get("primaryDomain", {}).get("host"),
            product_count=count
        )
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return ConnectResponse(success=False, error=str(e))


@app.post("/api/products")
async def get_products(request: ConnectRequest):
    """Get products from connected store."""
    try:
        client = ShopifyGraphQLClient(request.store_url, request.access_token)
        products = await client.list_all_products(batch_size=100, skip_ai_enhanced=False)
        
        return {
            "success": True,
            "count": len(products),
            "products": [
                {
                    "id": p.id,
                    "numeric_id": p.numeric_id,
                    "title": p.title,
                    "image_count": len(p.images),
                    "first_image": p.images[0]["url"] if p.images else None,
                    "has_ai_tag": p.has_ai_enhanced_tag,
                    "status": p.status
                }
                for p in products
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhance")
async def start_enhancement(request: EnhanceRequest, background_tasks: BackgroundTasks):
    """Start enhancement job."""
    if not gemini_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured on server")
    
    job_id = str(uuid.uuid4())
    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        current_product=0,
        total_products=0,
        start_time=datetime.now().isoformat()
    )
    active_jobs[job_id] = job_status
    
    background_tasks.add_task(
        run_enhancement_job,
        job_id,
        request.store_url,
        request.access_token,
        request.max_products,
        request.skip_ai_enhanced,
        request.delete_old_images
    )
    
    return {"job_id": job_id, "status": "started"}


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of an enhancement job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return active_jobs[job_id]


@app.post("/api/stop/{job_id}")
async def stop_job(job_id: str):
    """Stop a running enhancement job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    active_jobs[job_id].status = "stopping"
    return {"status": "stopping"}


# ============================================
# Background Task
# ============================================

async def run_enhancement_job(
    job_id: str,
    store_url: str,
    access_token: str,
    max_products: Optional[int],
    skip_ai_enhanced: bool,
    delete_old_images: bool
):
    """Run enhancement in background."""
    job = active_jobs[job_id]
    start_time = datetime.now()
    
    try:
        job.status = "running"
        enhancer = PhotoEnhancer(store_url, access_token, gemini_keys)
        
        def on_progress(completed: int, total: int, product_title: str):
            job.current_product = completed
            job.total_products = total
            job.progress = int(completed / total * 100) if total > 0 else 0
            job.current_product_title = product_title
            
            elapsed = (datetime.now() - start_time).total_seconds()
            if completed > 0:
                rate = elapsed / completed
                remaining = total - completed
                job.eta_seconds = rate * remaining
        
        enhancer.set_progress_callback(on_progress)
        
        async def check_stop():
            while enhancer.is_running:
                if job.status == "stopping":
                    enhancer.stop()
                    break
                await asyncio.sleep(0.5)
        
        stop_task = asyncio.create_task(check_stop())
        result = await enhancer.enhance_store(
            max_products=max_products,
            skip_ai_enhanced=skip_ai_enhanced,
            delete_old_images=delete_old_images
        )
        stop_task.cancel()
        
        job_results[job_id] = result
        job.result = result.to_dict()
        job.status = "completed"
        job.progress = 100
        
        logger.info(f"Job {job_id} completed: {result.successful_products}/{result.total_products}")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job.status = "failed"
        job.error = str(e)


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True, log_level="info")

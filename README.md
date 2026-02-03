# Lumina Photo Enhancer

AI-powered Shopify product image enhancement using Gemini 2.5 Flash.

## Features

- 🔗 Connect to any Shopify store via GraphQL API
- 🖼️ Enhance product images with AI-generated model photos
- ⚡ Parallel processing with 10+ Gemini API keys (150+ images/min)
- 🏷️ Automatic "ai-enhanced" tagging
- 📊 Real-time progress tracking via WebSocket

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Copy example and edit
cp .env.example .env

# Add your Gemini API keys (10 recommended for speed)
GEMINI_API_KEY_1=xxx
GEMINI_API_KEY_2=xxx
# ... up to 10
```

### 3. Run Locally

```bash
# Start the server
python server.py

# Open http://localhost:8000/app in browser
```

## Deployment

### Backend (Render)

1. Create new Web Service on [Render](https://render.com)
2. Connect your GitHub repo
3. Set environment variables (all 10 Gemini keys)
4. Deploy with `starter` plan (512MB) - upgrade if needed

### Frontend (Vercel)

1. Import project on [Vercel](https://vercel.com)
2. It will auto-detect the `vercel.json` config
3. Deploy
4. Update `API_BASE_URL` in `frontend/app.js` with your Render URL

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/connect` | POST | Validate Shopify connection |
| `/api/products` | POST | List products from store |
| `/api/enhance` | POST | Start enhancement job |
| `/api/status/{job_id}` | GET | Get job progress |
| `/api/stop/{job_id}` | POST | Stop running job |
| `/ws/progress/{job_id}` | WS | Real-time progress |

## Performance

With 10 Gemini API keys:
- **Theoretical max**: 150 images/minute
- **3000 products**: ~20-25 minutes

## Files

```
lumina-photo-gen/
├── server.py              # FastAPI server
├── photo_enhancer.py      # Main orchestrator
├── parallel_gemini.py     # Multi-key Gemini processor
├── shopify_graphql.py     # Shopify GraphQL client
├── shopify_queries.py     # GraphQL queries
├── shopify_mutations.py   # GraphQL mutations
├── frontend/
│   ├── index.html         # Web UI
│   ├── styles.css         # Styling
│   └── app.js             # Frontend logic
├── render.yaml            # Render deployment config
├── vercel.json            # Vercel deployment config
└── requirements.txt       # Python dependencies
```

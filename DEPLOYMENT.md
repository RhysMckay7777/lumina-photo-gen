# CatVTON Production Deployment Guide

Complete guide for deploying CatVTON for product photo generation at scale.

---

## Architecture

```
┌─────────────────────┐
│ AliExpress Scraper  │
│ (dropship-automate) │
└──────────┬──────────┘
           │
           │ scraped_products.json
           ▼
┌─────────────────────┐
│ Production Pipeline │
│ (production_pipeline.py) │
└──────────┬──────────┘
           │
           │ API calls
           ▼
┌─────────────────────┐
│   CatVTON Server    │
│   (RunPod GPU)      │
└──────────┬──────────┘
           │
           │ generated images
           ▼
┌─────────────────────┐
│  Generated Photos   │
│  (ready for upload) │
└─────────────────────┘
```

---

## Step 1: Deploy CatVTON to RunPod

### Option A: Automated (Recommended)

```bash
cd ~/lumina-photo-gen
python deploy_runpod.py --api-key YOUR_RUNPOD_API_KEY
```

### Option B: Manual

1. **Sign up for RunPod**: https://runpod.io

2. **Create GPU Pod**:
   - Go to https://runpod.io/console/pods
   - Click "Deploy" → "GPU Pod"
   - Select: **NVIDIA RTX 4090**
   - Template: **PyTorch 2.1.0**
   - Disk: **50GB**
   - Ports: Expose **7860**
   - Click "Deploy"

3. **Wait for pod to start** (~2 minutes)

4. **SSH into pod**:
   ```bash
   ssh root@your-pod-ip
   ```

5. **Run setup script**:
   ```bash
   cd /workspace
   git clone https://github.com/Zheng-Chong/CatVTON.git
   cd CatVTON
   
   # Install dependencies
   pip install -r requirements.txt
   pip install fastapi uvicorn
   
   # Copy API server
   # (upload api_server.py to the pod)
   
   # Start API server
   python api_server.py
   ```

6. **Get your pod URL**:
   - Format: `https://YOUR-POD-ID.runpod.net`
   - Save this for Step 2

---

## Step 2: Prepare Model Photos

Download stock photos of women aged 40-65 for your demographic.

### Directory Structure

```
~/lumina-photo-gen/model_photos/
├── woman_40_65_caucasian_standing_01.jpg
├── woman_40_65_caucasian_standing_02.jpg
├── woman_40_65_asian_standing_01.jpg
├── woman_40_65_black_standing_01.jpg
├── woman_40_65_hispanic_standing_01.jpg
└── ...
```

### Naming Convention

`{gender}_{age_min}_{age_max}_{ethnicity}_{pose}_{number}.jpg`

Example: `woman_40_65_caucasian_standing_01.jpg`

### Where to Get Stock Photos

- **Pexels**: https://pexels.com (free, commercial use)
- **Unsplash**: https://unsplash.com (free, commercial use)
- **Shutterstock**: Paid, high quality
- **Custom photoshoot**: Best quality control

### Recommended Setup

- **Minimum**: 5-10 diverse models
- **Recommended**: 20-30 models
- **Diversity**: Mix of ages, ethnicities, body types
- **Poses**: Standing, neutral expression, full body visible
- **Background**: Plain/simple (white, gray, or will be removed)

---

## Step 3: Run Production Pipeline

### Basic Usage

```bash
cd ~/lumina-photo-gen

python production_pipeline.py \
  --catvton-url https://YOUR-POD-ID.runpod.net \
  --model-photos ~/lumina-photo-gen/model_photos \
  --scraper-output ../dropship-automate/scraped_products.json \
  --output-dir ~/lumina-photo-gen/generated \
  --variants 3
```

### Parameters

- `--catvton-url`: Your RunPod pod URL
- `--model-photos`: Directory with model/person photos
- `--scraper-output`: JSON from AliExpress scraper
- `--output-dir`: Where to save generated images
- `--variants`: Number of model variants per product (default: 3)

### Output

Generated images saved to `--output-dir` with naming:
- `{product_id}_variant1.jpg`
- `{product_id}_variant2.jpg`
- `{product_id}_variant3.jpg`

Plus manifest file: `generation_manifest.json`

---

## Step 4: Cost Management

### RunPod Costs

**RTX 4090**: $0.34/hour

### Cost Calculation

- **Generation time**: ~11 seconds per image (FLUX version)
- **1000 images**: 11,000 seconds = 3.05 hours
- **Cost**: 3.05 × $0.34 = **$1.04 per 1000 images**

### Cost Optimization Tips

1. **Batch processing**: Generate images in batches to keep pod running efficiently
2. **Stop pod when idle**: Don't leave it running overnight
3. **Use spot instances**: Cheaper but can be interrupted
4. **Process in bulk**: Run large batches (5k-10k images) to maximize efficiency

### Monthly Cost Examples

| Products/Month | Images Generated | GPU Hours | Cost |
|----------------|------------------|-----------|------|
| 100 | 300 | 0.9 | $0.31 |
| 500 | 1,500 | 4.5 | $1.53 |
| 1,000 | 3,000 | 9.2 | $3.13 |
| 5,000 | 15,000 | 45.8 | $15.57 |
| 10,000 | 30,000 | 91.7 | $31.18 |

---

## Step 5: Integration with Shopify

### Option A: Manual Upload

1. Generated images in `~/lumina-photo-gen/generated/`
2. Upload to Shopify product pages manually

### Option B: Automated Upload (Future)

```bash
python shopify_upload.py \
  --generated-dir ~/lumina-photo-gen/generated \
  --manifest generation_manifest.json \
  --shopify-api-key YOUR_KEY
```

*(Script to be built)*

---

## Monitoring & Maintenance

### Health Checks

Check if CatVTON server is running:

```bash
curl https://YOUR-POD-ID.runpod.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true
}
```

### Logs

SSH into pod and check logs:

```bash
ssh root@your-pod-ip
cd /workspace/CatVTON
tail -f api_server.log
```

### Restart Server

If server becomes unresponsive:

```bash
ssh root@your-pod-ip
cd /workspace/CatVTON
pkill -f api_server.py
python api_server.py
```

---

## Scaling

### For High Volume (10k+ products)

1. **Multiple GPU pods**: Deploy 2-3 pods, round-robin requests
2. **Larger GPU**: RTX 6000 Ada or A100 for faster generation
3. **Local GPU server**: Buy/rent dedicated hardware for $100-200/month

### Load Balancing

```python
# Distribute across multiple pods
pod_urls = [
    "https://pod1.runpod.net",
    "https://pod2.runpod.net",
    "https://pod3.runpod.net"
]

# Rotate requests
for idx, product in enumerate(products):
    pod_url = pod_urls[idx % len(pod_urls)]
    generate(pod_url, product)
```

---

## Troubleshooting

### "Model not loaded" error

Server still starting. Wait 2-3 minutes for model weights to download on first run.

### Generation takes too long (>30s)

- Check GPU availability: `nvidia-smi`
- Restart server
- Try different guidance_scale (lower = faster)

### Out of memory error

- Reduce resolution
- Use bf16 precision (already default)
- Upgrade to 24GB GPU

### Poor quality results

- Use higher-res input images (1024x768+)
- Try different model photos
- Adjust guidance_scale (2.0-3.5 range)

---

## Security & Privacy

### Important Notes

1. **Don't expose pod publicly without authentication**
2. **Product images**: Use local processing, don't upload to third parties
3. **Model photos**: Ensure you have rights to use stock photos
4. **Generated images**: You own the output

### Add API Authentication (Optional)

```python
# In api_server.py, add:
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/generate")
async def generate_tryon(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    ...
):
    if credentials.credentials != "YOUR_SECRET_TOKEN":
        raise HTTPException(status_code=401)
    ...
```

---

## Next Steps

1. ✅ Deploy CatVTON to RunPod
2. ✅ Prepare model photos
3. ✅ Run test generation on 10 products
4. ✅ Evaluate quality
5. ✅ Scale to full catalog
6. Build Shopify auto-upload integration

---

**Ready to deploy? Start with Step 1.**

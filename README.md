# AI Product Photo Generator

**Purpose**: Generate professional lifestyle product photos using AI virtual try-on technology.

**Target**: Dropshipping business - transform AliExpress product images into lifestyle photos with models.

---

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Cost** | $1.04 per 1000 images |
| **Speed** | 11 seconds per image |
| **Quality** | State-of-the-art (ICLR 2025) |
| **GPU Required** | NVIDIA RTX 4090 (cloud rental) |
| **Model** | CatVTON-FLUX |

---

## 📁 Project Structure

```
lumina-photo-gen/
├── README.md                    # This file
├── RESEARCH.md                  # Solution comparison & analysis
├── DEPLOYMENT.md                # Production deployment guide
├── STATUS.md                    # Current setup status
├── SETUP_GUIDE.md               # CatVTON setup guide
├── IMAGE_LIBRARY_GUIDE.md       # 🆕 Multi-store image library guide
│
├── CatVTON/                     # Cloned repository
│   ├── api_server.py            # Production API server
│   ├── batch_process.py         # Batch processing script
│   └── app_flux.py              # Gradio app (FLUX version)
│
├── production_pipeline.py       # 🔄 Updated with library integration
├── image_library.py             # 🆕 Airtable library manager
├── sync_to_store.py             # 🆕 Multi-store sync tool
├── airtable_setup.md            # 🆕 Airtable setup instructions
├── deploy_runpod.py             # RunPod deployment automation
├── runpod_setup.sh              # Setup script for GPU instance
│
├── model_photos/                # Stock photos (women 40-65)
├── generated/                   # Generated product photos
└── catvton_client.py            # Python client for API
```

---

## 🚀 Quick Start

### 1. Deploy to Cloud GPU

```bash
cd ~/lumina-photo-gen
python deploy_runpod.py --api-key YOUR_RUNPOD_API_KEY
```

### 2. Prepare Model Photos

Download stock photos to `model_photos/` directory:
- Women aged 40-65
- Diverse ethnicities/body types
- Full body, standing poses
- Plain backgrounds

### 3. Run Production Pipeline

```bash
python production_pipeline.py \
  --catvton-url https://YOUR-POD-ID.runpod.net \
  --model-photos ~/lumina-photo-gen/model_photos \
  --scraper-output ../dropship-automate/scraped_products.json \
  --output-dir ~/lumina-photo-gen/generated \
  --variants 3
```

---

## 💰 Cost Analysis

### CatVTON (Self-Hosted)

- **Setup**: One-time ($0, just RunPod account)
- **Runtime**: $0.34/hour (RTX 4090)
- **Per 1000 images**: ~$1.04
- **Savings vs Fashn.ai**: 97-99%

### Fashn.ai (API Alternative)

- **Per 1000 images**: $40-75
- **Pros**: No setup, commercial license, instant start
- **Cons**: 40-75x more expensive

### Recommendation for Scale

| Volume | Recommended Solution | Monthly Cost |
|--------|---------------------|--------------|
| <1,000 images | Fashn.ai | $40-75 |
| 1,000-5,000 | CatVTON (test, then decide) | $1-5 |
| 5,000+ | CatVTON (self-hosted) | $5-30 |
| 10,000+ | CatVTON (dedicated GPU) | $30-100 |

---

## 🎯 Use Cases

### Dropshipping Product Photos

**Input**: AliExpress product image (garment on white background)

**Output**: Professional lifestyle photo (model wearing product)

**Benefits**:
- Increase conversion rates (professional photos)
- Differentiate from competitors (unique images)
- Target specific demographics (women 40-65)
- Scale cheaply (pennies per image)

### Example Workflow

1. Scrape 100 products from AliExpress
2. Generate 3 model variants per product = 300 images
3. Cost: $0.31
4. Time: ~55 minutes
5. Upload to Shopify automatically

---

## 🗄️ NEW: Multi-Store Image Library

**Reuse generated images across unlimited stores!**

### The Problem
Running 5 stores with same products? Without a library:
- Generate 1,000 products × 5 stores = **5,000 generations**
- Cost: **$5.20**
- Time: **15 hours**

### The Solution
With Airtable image library:
- Generate 1,000 products **once**
- Reuse 90% across other stores
- Cost: **$1.22** (76% savings)
- Time: **3.6 hours** (76% time saved)

### How It Works
```bash
# Store 1: Generate & save to library
python production_pipeline.py --use-library

# Store 2-10: Reuse from library
python sync_to_store.py --store-name "Store2" --csv products.csv
```

### Features
✅ Automatic deduplication  
✅ Track which stores use which images  
✅ Sync to new stores in minutes  
✅ Visual Airtable interface  
✅ Free plan supports 400 products

**Full guide**: See [IMAGE_LIBRARY_GUIDE.md](IMAGE_LIBRARY_GUIDE.md)

---

## 📚 Documentation

- **[RESEARCH.md](RESEARCH.md)**: Comparison of all virtual try-on solutions
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Complete deployment guide
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: CatVTON technical setup
- **[STATUS.md](STATUS.md)**: Current setup status & blockers

---

## 🔧 Technical Details

### Model: CatVTON-FLUX

- **Architecture**: Single UNet with FLUX.1-Fill-dev
- **Parameters**: 899M total, 49M trainable
- **Quality**: SOTA on VITON-HD benchmark
- **Speed**: 11 seconds/image (A100), 15-20s (RTX 4090)
- **Resolution**: 1024×768 native
- **VRAM**: ~8GB with bf16 precision

### Requirements

- **GPU**: NVIDIA with 8GB+ VRAM
- **Python**: 3.9+
- **CUDA**: 11.8+
- **Disk**: 50GB (for models + outputs)

---

## ⚠️ Important Notes

### Licensing

CatVTON uses **CC BY-NC-SA 4.0** license (non-commercial).

**What this means:**
- ✅ OK for research & testing
- ✅ OK for personal projects
- ❌ Requires commercial license for business use

**Options:**
1. Use for testing/research only
2. Negotiate commercial license with creators
3. Use Fashn.ai API (commercial license included)
4. Use DCI-VTON (MIT license, lower quality)

**Deployment decision**: Your responsibility

### Data Privacy

- All processing happens on your GPU instance
- Product images never leave your infrastructure
- Model photos: Ensure you have usage rights
- Generated images: You own the outputs

---

## 🛠️ Built Components

✅ **API Server** (`api_server.py`)
- REST API for generation
- Batch processing endpoint
- Health checks
- Result storage

✅ **Production Pipeline** (`production_pipeline.py`)
- Integrates with dropship-automate scraper
- Manages model photo selection
- Batch processing with progress tracking
- Generates variants per product
- Saves manifest for tracking

✅ **Deployment Automation** (`deploy_runpod.py`)
- RunPod provisioning
- Automatic setup
- Client generation

✅ **Batch Processor** (`batch_process.py`)
- Process directories of images
- Progress tracking
- Error handling
- Stats reporting

---

## 📈 Scaling

### For 10,000+ Products

**Option 1**: Multiple GPU pods (load balancing)
- Deploy 2-3 RTX 4090 pods
- Round-robin requests
- Cost: ~3x single pod

**Option 2**: Larger GPU
- A100 (40GB): Faster generation
- Cost: $1.10/hour vs $0.34/hour

**Option 3**: Dedicated server
- Rent bare metal GPU server
- $100-200/month unlimited usage
- Best for sustained high volume

---

## 🎬 Next Steps

1. **Deploy**: Follow [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Test**: Generate 10-50 samples
3. **Evaluate**: Compare quality vs alternatives
4. **Scale**: Process full product catalog
5. **Integrate**: Auto-upload to Shopify
6. **Optimize**: Fine-tune for your specific products

---

## 📞 Support

For technical questions about:
- **CatVTON**: https://github.com/Zheng-Chong/CatVTON
- **RunPod**: https://runpod.io/support
- **Deployment**: See DEPLOYMENT.md troubleshooting

---

**Status**: ✅ Complete & ready to deploy

**Decision**: User's choice to deploy commercially or for testing

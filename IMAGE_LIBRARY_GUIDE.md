# Image Library System - Complete Guide

**Purpose**: Reuse generated product images across multiple Shopify stores

**Benefit**: Generate once, use everywhere. Save time & money.

---

## 🎯 How It Works

```
┌────────────────────────────────────────────┐
│ First Store - Generate 1,000 Products     │
│ Cost: ~$1 (CatVTON) or $40-75 (Fashn.ai)  │
│ Time: ~3 hours                             │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Airtable Library   │
        │  Stores all images  │
        └─────────┬───────────┘
                  │
        ┌─────────┴─────────┬──────────────┬──────────────┐
        │                   │              │              │
        ▼                   ▼              ▼              ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Store 2     │   │  Store 3     │   │  Store 4     │   │  Store 5     │
│  Reuse 80%   │   │  Reuse 85%   │   │  Reuse 90%   │   │  Reuse 95%   │
│  Cost: $0.20 │   │  Cost: $0.15 │   │  Cost: $0.10 │   │  Cost: $0.05 │
│  Time: 10min │   │  Time: 5min  │   │  Time: 3min  │   │  Time: 2min  │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 📋 Setup (One-Time)

### Step 1: Create Airtable Account

1. Go to https://airtable.com/signup
2. Sign up (free plan is fine for testing)
3. Verify email

### Step 2: Set Up Base

Follow instructions in `airtable_setup.md`:
- Create "Product Image Library" base
- Add 3 tables: Products, Generated Images, Store Usage
- Configure fields as specified

### Step 3: Get Credentials

1. **API Token**: https://airtable.com/create/tokens
   - Create token with read/write access
   - Copy token (starts with `pat...`)

2. **Base ID**: From your base URL
   - Format: `appXXXXXXXXXXXXXX`

3. Set environment variables:
   ```bash
   export AIRTABLE_API_KEY="patXXXXXXXXXXXXXXX"
   export AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
   ```

---

## 🚀 Usage

### Scenario 1: First Store (Generate & Save)

```bash
# Generate images and auto-save to library
python production_pipeline.py \
  --catvton-url https://your-pod.runpod.net \
  --scraper-output products.json \
  --use-library \
  --variants 3
```

**What happens:**
1. Checks library for each product
2. If not found → generates images
3. Saves to Airtable library automatically
4. Saves to local disk

**Result**: 1,000 products × 3 variants = 3,000 images saved

---

### Scenario 2: New Store (Reuse Existing)

```bash
# Check library first, only generate new ones
python production_pipeline.py \
  --catvton-url https://your-pod.runpod.net \
  --scraper-output store2_products.json \
  --use-library \
  --skip-existing \
  --variants 3
```

**What happens:**
1. Checks library for each product
2. If found → reuses existing images (instant)
3. If not found → generates new images
4. Saves new images to library

**Expected**:
- 800 products reused (instant)
- 200 products generated (~30 minutes)
- **Time saved**: ~2.5 hours
- **Cost saved**: ~$0.80

---

### Scenario 3: Sync to Shopify Store

```bash
# Upload images from library to Shopify
python sync_to_store.py \
  --store-name "My Second Store" \
  --shopify-url https://store2.myshopify.com \
  --csv products_mapping.csv
```

**CSV format:**
```csv
CJ Product ID,Shopify Product ID
CJ12345678,8765432109876
CJ87654321,1234567890123
...
```

**What happens:**
1. Reads product IDs from CSV
2. Gets images from Airtable library
3. Uploads to Shopify product
4. Marks as "used in Store 2"

---

## 📊 Library Management

### Check Library Stats

```bash
python image_library.py --stats
```

**Output:**
```
📊 Library Statistics:
  Total Products: 1,247
  Products With Images: 1,247
  Total Images: 3,741
  Stores Using Library: 5
  Reuse Rate: 100.0%
```

### Check Specific Product

```bash
python image_library.py --check CJ12345678
```

**Output:**
```
CJ12345678: ✅ Has images
```

### Get Product Images

```bash
python image_library.py --get CJ12345678
```

**Output:**
```
📸 Images for CJ12345678:
  Variant 1: https://dl.airtable.com/.../image1.jpg
  Variant 2: https://dl.airtable.com/.../image2.jpg
  Variant 3: https://dl.airtable.com/.../image3.jpg
```

---

## 💰 Cost Comparison

### Without Library (Generate Every Time)

| Store | Products | Generation Cost | Time |
|-------|----------|----------------|------|
| Store 1 | 1,000 | $1.04 | 3.0h |
| Store 2 | 1,000 | $1.04 | 3.0h |
| Store 3 | 1,000 | $1.04 | 3.0h |
| Store 4 | 1,000 | $1.04 | 3.0h |
| Store 5 | 1,000 | $1.04 | 3.0h |
| **Total** | **5,000** | **$5.20** | **15.0h** |

### With Library (Reuse 90%)

| Store | Products | New | Reused | Cost | Time |
|-------|----------|-----|--------|------|------|
| Store 1 | 1,000 | 1,000 | 0 | $1.04 | 3.0h |
| Store 2 | 1,000 | 100 | 900 | $0.10 | 20m |
| Store 3 | 1,000 | 50 | 950 | $0.05 | 10m |
| Store 4 | 1,000 | 20 | 980 | $0.02 | 5m |
| Store 5 | 1,000 | 10 | 990 | $0.01 | 2m |
| **Total** | **5,000** | **1,180** | **3,820** | **$1.22** | **3.6h** |

**Savings**: $3.98 (76%) and 11.4 hours (76%)

---

## 🗄️ Airtable Plan Comparison

| Plan | Price | Records | Storage | Good For |
|------|-------|---------|---------|----------|
| **Free** | $0 | 1,200 | 2GB | ~400 products (testing) |
| **Plus** | $20/mo | 5,000 | 5GB | ~1,600 products |
| **Pro** | $45/mo | 50,000 | 20GB | ~16,000 products |

**Recommendation**:
- Testing: Free plan
- 1-5 stores: Plus plan ($20/mo)
- 10+ stores: Pro plan ($45/mo)

---

## 🔍 Example Workflows

### Workflow 1: Launch 3 Stores Same Day

**Day 1 Morning**: Generate images for Store 1
```bash
python production_pipeline.py --use-library --scraper-output store1.json
```
**Result**: 1,000 products, 3,000 images saved to library

**Day 1 Afternoon**: Sync to Store 2
```bash
python sync_to_store.py --store-name "Store2" --csv store2.csv
```
**Result**: 950 reused, 50 generated (15 minutes total)

**Day 1 Evening**: Sync to Store 3
```bash
python sync_to_store.py --store-name "Store3" --csv store3.csv
```
**Result**: 980 reused, 20 generated (8 minutes total)

**Total Time**: 3.5 hours (vs 9 hours without library)
**Total Cost**: $1.15 (vs $3.12 without library)

---

### Workflow 2: Add Products to Existing Stores

**Scenario**: Add 200 new products to all 5 stores

**Without Library**:
- Generate 200 × 5 = 1,000 times
- Cost: $1.04
- Time: 3 hours

**With Library**:
- Generate 200 once
- Sync to 4 stores (instant)
- Cost: $0.21
- Time: 35 minutes

**Savings**: $0.83 and 2.5 hours

---

## 🛠️ Advanced Features

### Custom Model Selection

Store which models were used for which products:
```python
library.save_images(
    cj_product_id="CJ12345678",
    image_paths=[img1, img2, img3],
    model_photos=["woman_45_caucasian", "woman_50_asian", "woman_60_black"],
    generation_method="CatVTON"
)
```

### Quality Rating

Rate images in Airtable (1-5 stars) to track best performers.

### Store Performance Tracking

See which stores use which products via Store Usage table.

### Batch Operations

Process thousands of products efficiently:
```python
from image_library import ImageLibrary

library = ImageLibrary()

# Batch check
products = ["CJ001", "CJ002", "CJ003", ...]
existing = [p for p in products if library.has_images(p)]
new = [p for p in products if not library.has_images(p)]

print(f"Reusing {len(existing)}, generating {len(new)}")
```

---

## 🚨 Troubleshooting

### Error: "AIRTABLE_API_KEY not found"

**Fix**:
```bash
export AIRTABLE_API_KEY="patXXXXXXXXXXXXXXX"
export AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
```

### Error: "Table not found"

**Fix**: Check table names match exactly:
- `Products` (not "Product" or "products")
- `Generated Images`
- `Store Usage`

### Images not uploading to Airtable

**Note**: Airtable attachments require either:
1. Public URL to image
2. Upload via file upload

**Current system**: Stores local paths, use cloud storage (S3/R2) for URLs

### Library shows 0 products

**Check**:
1. API credentials are correct
2. Base ID is correct
3. Tables are created
4. You've run pipeline with `--use-library`

---

## 🎯 Best Practices

1. **Always use library** for production (set `--use-library`)
2. **Check stats regularly** to track reuse rate
3. **Rate image quality** in Airtable to improve selection
4. **Tag products by category** for better organization
5. **Backup Airtable weekly** (export to CSV)

---

## 📈 ROI Calculator

**Your metrics:**
- Number of stores: ___
- Products per store: ___
- Overlap between stores: ___% (typically 80-90%)

**Estimated savings:**
- Without library: Products × Stores × $0.001 = $___
- With library: Products × (1 + (Stores-1) × (1-Overlap)) × $0.001 = $___
- **You save**: $___

**Time savings:**
- Without library: Products × Stores × 11s = ___ hours
- With library: Products × (1 + (Stores-1) × (1-Overlap)) × 11s = ___ hours
- **You save**: ___ hours

---

## 📞 Support

**Airtable issues**: https://support.airtable.com
**Image library code**: Check `image_library.py`
**Sync issues**: Check `sync_to_store.py`

---

**Status**: ✅ Complete and ready to use

**Next step**: Follow `airtable_setup.md` to create your base

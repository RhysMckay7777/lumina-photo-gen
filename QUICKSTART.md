# 🚀 Quick Start Guide

Get your first AI-generated product photo in 5 minutes!

---

## Step 1: Get API Key (2 minutes)

1. Go to https://fashn.ai
2. Sign up for an account
3. Navigate to API settings
4. Copy your API key

💡 **Tip:** Fashn.ai offers a free trial with credits to test the service.

---

## Step 2: Install (1 minute)

```bash
cd ~/lumina-photo-gen

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Configure (1 minute)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env
```

**Add your API key:**
```bash
FASHN_API_KEY=your_actual_api_key_here
```

Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

---

## Step 4: Test Setup (30 seconds)

```bash
python test.py
```

**Expected output:**
```
🧪 LUMINA PHOTO GENERATOR - SETUP TEST
============================================================
🔑 Testing API key configuration...
✅ API key found: sk_live_xx...xxxx

📁 Testing directories...
✅ output/ ready
✅ downloads/ ready
✅ reports/ ready

📦 Testing dependencies...
✅ requests
✅ PIL (Pillow)
✅ aiohttp
✅ tqdm

🎨 Testing generator initialization...
✅ Generator initialized successfully

============================================================
📊 TEST SUMMARY
============================================================
✅ Passed: 4/4
❌ Failed: 0/4

🎉 All tests passed! You're ready to generate photos!
```

---

## Step 5: Generate Your First Photo! (30 seconds)

### Option A: Use a sample image

Download a product image from AliExpress and save it as `product.jpg`, then:

```bash
python src/fashn_generator.py product.jpg
```

### Option B: Test with multiple images

```bash
python src/fashn_generator.py image1.jpg image2.jpg image3.jpg
```

**Expected output:**
```
🎨 Generating photo for product.jpg...
✅ Generated in 7.2s: output/product_generated_1738096800.jpg

✅ Success! Image saved to: output/product_generated_1738096800.jpg
💰 Cost: $0.075
```

Your generated image is now in the `output/` folder! 🎉

---

## Next Steps

### Test with Different Settings

```bash
# Generate a dress with lifestyle background
python src/fashn_generator.py dress.jpg --category dresses --background lifestyle

# Generate a top with studio background
python src/fashn_generator.py top.jpg --category tops --background studio

# Generate outerwear with outdoor background
python src/fashn_generator.py jacket.jpg --category outerwear --background outdoor
```

### Batch Process Multiple Products

Create a JSON file with your products:

```json
{
  "products": [
    {
      "id": "product_001",
      "image_url": "https://example.com/product1.jpg",
      "title": "Summer Dress",
      "category": "dresses"
    },
    {
      "id": "product_002",
      "image_url": "https://example.com/product2.jpg",
      "title": "Casual Top",
      "category": "tops"
    }
  ]
}
```

Then run:

```bash
python src/batch_processor.py products.json
```

### Integrate with Your Scraper

See [README.md](README.md#-api-integration) for integration examples.

---

## Troubleshooting

### "API key not found"

Make sure:
1. `.env` file exists in the project root
2. `FASHN_API_KEY` is set in `.env`
3. No quotes around the API key value

### "Module not found"

Run: `pip install -r requirements.txt`

### Image generation failed

Check:
- Image format is JPG, PNG, or WEBP
- Image is not corrupted
- File path is correct
- API key is valid

---

## Cost Examples

### Small Test (10 images)
- Cost: $0.75
- Time: ~70 seconds (7s per image)

### Medium Batch (100 images)
- Cost: $7.50
- Time: ~12 minutes

### Large Batch (1,000 images)
- Cost: $75 ($40-50 with volume discount)
- Time: ~2 hours

---

## Tips for Best Results

1. **Use high-quality product images**
   - Resolution: 1024px or higher
   - Clear, well-lit product photos
   - Minimal background clutter

2. **Choose the right category**
   - `tops` - Shirts, blouses, t-shirts
   - `bottoms` - Pants, skirts, shorts
   - `dresses` - Dresses, gowns
   - `outerwear` - Jackets, coats, cardigans

3. **Select appropriate background**
   - `lifestyle` - Natural settings, home environments (best for casual wear)
   - `studio` - Clean, professional look (best for formal wear)
   - `outdoor` - Nature, urban settings (best for outerwear)

4. **Target the right demographic**
   - `female_40_65` - Women aged 40-65 (your target)
   - Other options available for different demographics

---

## Ready to Scale?

Once you've tested and are happy with the results:

1. **Integrate with your scraper** - See [README.md](README.md#-integration-with-existing-scraper)
2. **Set up automation** - Process products automatically as they're scraped
3. **Request volume discounts** - Contact Fashn.ai for pricing at scale
4. **Monitor results** - Track conversion rates and ROI

---

## Need Help?

- 📚 Read the [full README](README.md)
- 🔍 See the [comparison table](COMPARISON.md)
- 📊 Review the [research report](research/solutions-research.md)
- 💬 Contact Fashn.ai support

---

**That's it! You're ready to transform your dropshipping business with AI-generated product photos! 🚀**

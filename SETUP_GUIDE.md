# CatVTON Setup Guide (Research/Testing)

**Purpose**: Virtual try-on for product photo generation  
**Model**: CatVTON-FLUX (State-of-the-art, 11 seconds per image)  
**License**: CC BY-NC-SA 4.0 (Non-commercial - research/testing only)

---

## Installation Steps

### 1. Create Environment
```bash
cd ~/lumina-photo-gen
conda create -n catvton python=3.9.0 -y
conda activate catvton
```

### 2. Install Requirements
```bash
cd ~/lumina-photo-gen/CatVTON
pip install -r requirements.txt
```

### 3. Run Gradio App (FLUX Version - Best Quality)
```bash
cd ~/lumina-photo-gen/CatVTON
CUDA_VISIBLE_DEVICES=0 python app_flux.py \
  --output_dir="resource/demo/output" \
  --mixed_precision="bf16" \
  --allow_tf32
```

**Note**: First run will auto-download model weights from HuggingFace (~several GB)

---

## Hardware Requirements

**Minimum**:
- GPU: 8GB VRAM (can run 1024x768 resolution with bf16 precision)
- Examples: RTX 3060 12GB, RTX 4060 Ti, M1 Mac (Metal)

**Recommended**:
- GPU: 16GB+ VRAM
- Examples: RTX 4080, RTX 4090, A100

**Mac Users (Apple Silicon)**:
- MPS backend supported
- M1/M2/M3 with 16GB+ unified memory should work

---

## Usage

### Via Gradio Web UI
1. Start app: `python app_flux.py`
2. Open browser to `http://127.0.0.1:7860`
3. Upload:
   - Person image (model wearing clothes)
   - Garment image (clothing item to try on)
4. Click "Generate"
5. Results save to `resource/demo/output/`

### Via Python Script (Batch Processing)
```python
from inference import run_inference

run_inference(
    person_image_path="path/to/person.jpg",
    garment_image_path="path/to/garment.jpg",
    output_path="output.jpg",
    mixed_precision="bf16"
)
```

---

## Performance

**CatVTON-FLUX (Best Quality)**:
- Speed: ~11 seconds per image (on A100)
- Resolution: 1024x768 native
- Quality: ⭐⭐⭐⭐⭐ (SOTA on VITON-HD benchmark)
- VRAM: ~8GB with bf16

**Standard CatVTON**:
- Speed: ~35 seconds per image
- Resolution: 1024x768
- Quality: ⭐⭐⭐⭐
- VRAM: ~8GB with bf16

---

## Cost Estimation (Self-Hosted)

**GPU Rental Options**:
- RunPod RTX 4090: $0.34/hour
- Vast.ai RTX 4090: $0.30-0.50/hour
- Lambda Labs A100: $1.10/hour (overkill for this)

**Cost per 1000 images (FLUX)**:
- Generation time: 11s/image × 1000 = 11,000s = 3.05 hours
- RTX 4090 @ $0.34/hour = **$1.04 per 1000 images**

**vs Fashn.ai**: $40-75 per 1000 images

**Savings**: 97-99% cheaper if self-hosted!

---

## Integration with Dropshipping Pipeline

### Basic Workflow
```bash
# 1. Scrape product images from AliExpress (existing scraper)
# 2. Download person/model images (age 40-65 demographic)
# 3. Batch process with CatVTON:

cd ~/lumina-photo-gen
python batch_process.py \
  --input_dir ../dropship-automate/scraped_products/ \
  --model_dir models/women_40_65/ \
  --output_dir generated_photos/ \
  --batch_size 8
```

### Full Automation Script (Coming)
- Auto-download person stock images
- Match clothing type to appropriate model poses
- Batch processing with progress tracking
- Quality filtering
- Output ready for Shopify upload

---

## Troubleshooting

**Out of Memory Error**:
- Reduce resolution
- Use bf16 precision
- Reduce batch size
- Use GPU with more VRAM

**Slow Generation**:
- Use FLUX version (faster)
- Upgrade GPU
- Enable allow_tf32 flag

**Poor Quality Results**:
- Use higher resolution images as input
- Try different model checkpoints
- Adjust guidance scale in app settings

---

## Next Steps

1. ✅ Install environment
2. ✅ Run Gradio app and test with sample images
3. Test quality with AliExpress product images
4. Source stock photos of women 40-65
5. Build batch processing script
6. Integrate with existing scraper pipeline

---

**Notes:**
- Model weights auto-download on first run (~2-5GB)
- Gradio app runs on http://127.0.0.1:7860
- Results save to `resource/demo/output/` by default
- For commercial deployment, user must handle licensing separately

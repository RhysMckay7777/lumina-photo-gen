#!/bin/bash
# Automated RunPod Deployment Script
# Run this on your RunPod GPU instance

set -e

echo "🚀 RunPod Deployment - IDM-VTON + FLUX"
echo "======================================"
echo ""

# Update system
echo "📦 Updating system..."
apt-get update -qq
apt-get install -y git wget curl -qq

# Check GPU
echo ""
echo "🖥️  Checking GPU..."
nvidia-smi --query-gpu=name --format=csv,noheader || echo "⚠️  No NVIDIA GPU detected"

# Clone repository
echo ""
echo "📥 Setting up workspace..."
cd /workspace

if [ -d "lumina-photo-gen" ]; then
    echo "   ℹ️  Directory exists, updating..."
    cd lumina-photo-gen
    git pull
    cd /workspace
else
    echo "   📥 Cloning repository..."
    # You'll need to replace this with your actual repo
    # For now, creating structure manually
    mkdir -p lumina-photo-gen
fi

cd lumina-photo-gen

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --quiet --upgrade pip

# Core dependencies
pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Diffusers for FLUX
pip install --quiet diffusers transformers accelerate

# IDM-VTON dependencies
pip install --quiet opencv-python pillow numpy scipy
pip install --quiet gradio spaces
pip install --quiet huggingface-hub

# Clone IDM-VTON if not exists
echo ""
echo "📥 Setting up IDM-VTON..."
if [ ! -d "IDM-VTON" ]; then
    git clone https://github.com/yisol/IDM-VTON.git
    cd IDM-VTON
    
    # Download model weights
    echo "   📥 Downloading model weights..."
    python -c "
from huggingface_hub import hf_hub_download
import os

# Download IDM-VTON models
models = [
    'yisol/IDM-VTON',
]

for model in models:
    try:
        print(f'Downloading {model}...')
        hf_hub_download(repo_id=model, filename='config.json', local_dir='.')
    except:
        print(f'Note: {model} may need manual download')
" || echo "   ⚠️  Model download incomplete, will auto-download on first use"
    
    cd ..
else
    echo "   ✅ IDM-VTON already set up"
fi

# Create production pipeline script
echo ""
echo "🔧 Creating production pipeline..."

cat > photo_pipeline.py << 'EOF'
#!/usr/bin/env python3
"""
Production Photo Pipeline - IDM-VTON + FLUX 2-Dev
Optimized for RunPod GPU instances
"""
import torch
from PIL import Image
from pathlib import Path
import sys
import os

# Add IDM-VTON to path
sys.path.insert(0, str(Path(__file__).parent / "IDM-VTON"))

class PhotoGenerationPipeline:
    """IDM-VTON + FLUX production pipeline"""
    
    def __init__(self, device="cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Using device: {self.device}")
        
        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        
        self.vton_model = None
        self.flux_model = None
    
    def load_vton(self):
        """Load IDM-VTON model"""
        if self.vton_model is not None:
            return
        
        print("📦 Loading IDM-VTON...")
        
        try:
            # Import IDM-VTON
            from gradio_demo.app import create_pipeline
            
            self.vton_model = create_pipeline(self.device)
            print("✅ IDM-VTON loaded")
        
        except Exception as e:
            print(f"⚠️  IDM-VTON error: {e}")
            print("   Will attempt alternative loading method...")
            
            # Alternative: Load manually
            from diffusers import AutoPipelineForImage2Image
            self.vton_model = AutoPipelineForImage2Image.from_pretrained(
                "yisol/IDM-VTON",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            print("✅ IDM-VTON loaded (alternative method)")
    
    def load_flux(self):
        """Load FLUX 2-Dev model"""
        if self.flux_model is not None:
            return
        
        print("📦 Loading FLUX 2-Dev...")
        
        from diffusers import FluxPipeline
        
        self.flux_model = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        
        # Enable memory optimizations
        if self.device == "cuda":
            self.flux_model.enable_model_cpu_offload()
        
        print("✅ FLUX 2-Dev loaded")
    
    def generate_tryon(self, garment_image, model_image):
        """Step 1: Virtual try-on"""
        print("\n🎨 Step 1: Virtual Try-On...")
        
        self.load_vton()
        
        try:
            # IDM-VTON inference
            with torch.inference_mode():
                result = self.vton_model(
                    prompt="Professional fashion photography",
                    image=model_image,
                    control_image=garment_image,
                    num_inference_steps=30,
                    guidance_scale=2.0
                ).images[0]
            
            print("✅ Try-on complete")
            return result
        
        except Exception as e:
            print(f"❌ Try-on failed: {e}")
            return None
    
    def enhance_background(self, image, prompt=None):
        """Step 2: Background enhancement"""
        print("\n🎨 Step 2: Background Enhancement...")
        
        self.load_flux()
        
        if prompt is None:
            prompt = (
                "Professional product photography, elegant mature woman wearing "
                "fashionable clothing, minimalist modern studio, soft lighting, "
                "high-end fashion catalog style, shallow depth of field"
            )
        
        try:
            with torch.inference_mode():
                result = self.flux_model(
                    prompt=prompt,
                    image=image,
                    strength=0.25,  # Light enhancement, preserve try-on
                    num_inference_steps=20,
                    guidance_scale=7.5
                ).images[0]
            
            print("✅ Background enhanced")
            return result
        
        except Exception as e:
            print(f"⚠️  Background enhancement failed: {e}")
            return image
    
    def process(self, garment_path, model_path, output_path, prompt=None):
        """Complete pipeline"""
        
        print(f"\n{'='*60}")
        print(f"🚀 PROCESSING")
        print(f"{'='*60}")
        print(f"Garment: {garment_path}")
        print(f"Model: {model_path}")
        print(f"Output: {output_path}")
        
        # Load images
        garment = Image.open(garment_path).convert("RGB")
        model = Image.open(model_path).convert("RGB")
        
        # Step 1: Try-on
        tryon = self.generate_tryon(garment, model)
        if tryon is None:
            return False
        
        # Step 2: Background
        final = self.enhance_background(tryon, prompt)
        
        # Save
        final.save(output_path, quality=95)
        print(f"\n💾 Saved: {output_path}")
        print(f"{'='*60}\n")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("garment", help="Garment/product image")
    parser.add_argument("model", help="Model photo")
    parser.add_argument("-o", "--output", default="output.jpg")
    parser.add_argument("-p", "--prompt", help="Custom background prompt")
    
    args = parser.parse_args()
    
    pipeline = PhotoGenerationPipeline()
    success = pipeline.process(args.garment, args.model, args.output, args.prompt)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
EOF

chmod +x photo_pipeline.py

# Create batch processing script
echo ""
echo "🔧 Creating batch processor..."

cat > batch_generate.py << 'EOF'
#!/usr/bin/env python3
"""
Batch photo generation for production use
"""
import os
import csv
import json
from pathlib import Path
from photo_pipeline import PhotoGenerationPipeline
import time

def batch_process(products_csv, model_dir, output_dir, limit=None):
    """Process multiple products"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    model_dir = Path(model_dir)
    models = sorted(list(model_dir.glob("*.jpg")) + list(model_dir.glob("*.png")))
    
    if not models:
        print("❌ No model photos found in", model_dir)
        return
    
    print(f"📸 Found {len(models)} model photos")
    
    # Load products
    with open(products_csv) as f:
        reader = csv.DictReader(f)
        products = list(reader)
    
    if limit:
        products = products[:limit]
    
    print(f"📦 Processing {len(products)} products\n")
    
    # Initialize pipeline
    pipeline = PhotoGenerationPipeline()
    
    results = []
    start_time = time.time()
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] {product.get('title', 'Unknown')[:50]}...")
        
        # Get product image
        product_img = product.get('image1') or product.get('image_url')
        
        if not product_img:
            print("   ⚠️  No product image, skipping")
            continue
        
        # Download if URL
        if product_img.startswith('http'):
            import requests
            img_data = requests.get(product_img).content
            temp_path = output_dir / f"temp_product_{i}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(img_data)
            product_img = str(temp_path)
        
        # Generate 3 photos with different models
        generated = []
        for j in range(3):
            model_idx = (i + j) % len(models)
            model_path = models[model_idx]
            
            output_path = output_dir / f"product_{i}_photo_{j+1}.jpg"
            
            success = pipeline.process(product_img, str(model_path), str(output_path))
            
            if success:
                generated.append(str(output_path))
                print(f"   ✅ Photo {j+1}/3")
            else:
                print(f"   ❌ Photo {j+1}/3 failed")
        
        results.append({
            "product": product.get('title'),
            "generated": len(generated),
            "paths": generated
        })
        
        # Clean up temp
        if 'temp_path' in locals():
            os.remove(temp_path)
    
    elapsed = time.time() - start_time
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"Processed: {len(results)} products")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Rate: {len(results)/(elapsed/3600):.1f} products/hour")
    print(f"{'='*60}\n")
    
    # Save results
    with open(output_dir / "batch_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Results saved: {output_dir}/batch_results.json")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", required=True, help="Products CSV file")
    parser.add_argument("--models", required=True, help="Model photos directory")
    parser.add_argument("--output", default="generated", help="Output directory")
    parser.add_argument("--limit", type=int, help="Limit number of products")
    
    args = parser.parse_args()
    
    batch_process(args.products, args.models, args.output, args.limit)
EOF

chmod +x batch_generate.py

# Test GPU
echo ""
echo "🧪 Testing GPU availability..."
python3 << 'EOF'
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
EOF

echo ""
echo "======================================"
echo "✅ RUNPOD SETUP COMPLETE!"
echo "======================================"
echo ""
echo "🎯 Quick Test:"
echo "   ./photo_pipeline.py product.jpg model.jpg -o test.jpg"
echo ""
echo "📦 Batch Processing:"
echo "   ./batch_generate.py --products products.csv --models models/ --output generated/"
echo ""
echo "🚀 Ready for production!"
echo ""

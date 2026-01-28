#!/bin/bash
# CatVTON RunPod Setup Script
# Run this on a RunPod RTX 4090 instance

set -e

echo "🚀 Setting up CatVTON on RunPod..."

# Update system
apt-get update
apt-get install -y git wget

# Clone repository
cd /workspace
git clone https://github.com/Zheng-Chong/CatVTON.git
cd CatVTON

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA support
pip install torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121

# Install remaining requirements
pip install accelerate==0.31.0
pip install git+https://github.com/huggingface/diffusers.git
pip install matplotlib==3.9.1 numpy==1.26.4 opencv_python==4.10.0.84
pip install pillow==10.3.0 PyYAML==6.0.1 scipy==1.13.1
pip install scikit-image==0.24.0 tqdm==4.66.4 transformers==4.46.3
pip install fvcore==0.1.5.post20221221 cloudpickle==3.0.0
pip install omegaconf==2.3.0 pycocotools==2.0.8 av==12.3.0
pip install gradio==4.41.0 peft>=0.17.0 "huggingface_hub>=0.34.0,<2.0"

echo "✅ Installation complete!"
echo ""
echo "🎯 To start the Gradio app:"
echo "cd /workspace/CatVTON"
echo "source venv/bin/activate"
echo "python app_flux.py --output_dir='output' --mixed_precision='bf16' --allow_tf32"
echo ""
echo "📱 Access the app at:"
echo "https://<your-runpod-id>.runpod.net:7860"
echo ""
echo "Note: First run will download model weights (~2-5GB)"

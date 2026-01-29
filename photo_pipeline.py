#!/usr/bin/env python3
"""
Complete Photo Generation Pipeline
IDM-VTON → FLUX 2-Dev Background Enhancement
"""
import torch
from PIL import Image
from pathlib import Path
import sys

class PhotoGenerationPipeline:
    """Complete pipeline: Try-on + Background"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Using device: {self.device}")
        
        # Initialize IDM-VTON
        self.vton_model = self.load_idm_vton()
        
        # Initialize FLUX
        self.flux_model = self.load_flux()
    
    def load_idm_vton(self):
        """Load IDM-VTON model"""
        print("📦 Loading IDM-VTON...")
        
        sys.path.insert(0, str(Path("IDM-VTON")))
        
        # Import IDM-VTON modules
        try:
            from gradio_demo.app import load_model
            model = load_model(self.device)
            print("✅ IDM-VTON loaded")
            return model
        except Exception as e:
            print(f"⚠️  IDM-VTON load error: {e}")
            return None
    
    def load_flux(self):
        """Load FLUX 2-Dev model"""
        print("📦 Loading FLUX 2-Dev...")
        
        from diffusers import FluxPipeline
        
        model = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16
        )
        model = model.to(self.device)
        
        print("✅ FLUX 2-Dev loaded")
        return model
    
    def generate_tryon(self, garment_image, model_image):
        """Step 1: Virtual try-on with IDM-VTON"""
        print("\n🎨 Step 1: Virtual Try-On...")
        
        if not self.vton_model:
            print("❌ IDM-VTON not available")
            return None
        
        # IDM-VTON inference
        try:
            result = self.vton_model(
                garment_image=garment_image,
                model_image=model_image
            )
            
            print("✅ Try-on complete")
            return result
        
        except Exception as e:
            print(f"❌ Try-on failed: {e}")
            return None
    
    def enhance_background(self, tryon_image, prompt=None):
        """Step 2: Add realistic background with FLUX"""
        print("\n🎨 Step 2: Background Enhancement...")
        
        if prompt is None:
            prompt = (
                "Professional product photography, elegant mature woman wearing fashionable clothing, "
                "standing in a modern minimalist studio, soft natural lighting, clean aesthetic, "
                "high-end fashion catalog style, shallow depth of field, professional bokeh"
            )
        
        # FLUX enhancement
        try:
            # Convert try-on to proper format for FLUX
            enhanced = self.flux_model(
                prompt=prompt,
                image=tryon_image,
                strength=0.3,  # Keep most of original, just enhance background
                num_inference_steps=30,
                guidance_scale=7.5
            ).images[0]
            
            print("✅ Background enhanced")
            return enhanced
        
        except Exception as e:
            print(f"❌ Background enhancement failed: {e}")
            return tryon_image  # Return original if enhancement fails
    
    def process(self, garment_path, model_path, output_path, 
                background_prompt=None):
        """Complete pipeline: Try-on → Background"""
        
        print(f"\n{'='*60}")
        print(f"🚀 PROCESSING PHOTO GENERATION")
        print(f"{'='*60}")
        print(f"Garment: {garment_path}")
        print(f"Model: {model_path}")
        print(f"Output: {output_path}")
        
        # Load images
        garment = Image.open(garment_path)
        model = Image.open(model_path)
        
        # Step 1: Try-on
        tryon_result = self.generate_tryon(garment, model)
        
        if tryon_result is None:
            print("❌ Pipeline failed at try-on step")
            return False
        
        # Step 2: Background
        final_result = self.enhance_background(tryon_result, background_prompt)
        
        # Save
        final_result.save(output_path)
        print(f"\n💾 Saved: {output_path}")
        print(f"{'='*60}\n")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="IDM-VTON + FLUX Photo Generation Pipeline"
    )
    parser.add_argument("garment", help="Path to garment/product image")
    parser.add_argument("model", help="Path to model photo")
    parser.add_argument("--output", "-o", default="output.jpg",
                       help="Output path")
    parser.add_argument("--prompt", "-p", 
                       help="Custom background prompt for FLUX")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = PhotoGenerationPipeline()
    
    # Process
    success = pipeline.process(
        args.garment,
        args.model,
        args.output,
        args.prompt
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

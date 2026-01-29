#!/usr/bin/env python3
"""
Hybrid AI Model Photo Generator
Step 1: Generate professional base model with Gemini
Step 2: Use IDM-VTON to put product on that model
"""
import os
import sys
import requests
import time
from pathlib import Path

# Import Gemini generator
try:
    from google import genai
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai"], check=True)
    from google import genai

class HybridGenerator:
    def __init__(self, gemini_key=None, replicate_token=None):
        self.gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY")
        self.replicate_token = replicate_token or os.environ.get("REPLICATE_API_TOKEN")
        
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not set")
        if not self.replicate_token:
            raise ValueError("REPLICATE_API_TOKEN not set")
        
        self.gemini_client = genai.Client(api_key=self.gemini_key)
        self.gemini_model = "gemini-2.5-flash-image"
    
    def generate_base_model(self, demographic="women-50-60", output_path=None):
        """
        Step 1: Generate professional base model with Gemini
        Plain clothing, white background, ready for virtual try-on
        """
        demographics = {
            "women-40-50": {
                "description": "elegant woman aged 45",
                "hair": "shoulder-length styled hair",
            },
            "women-50-60": {
                "description": "elegant mature woman aged 55",
                "hair": "silver-gray styled hair",
            },
            "women-60-65": {
                "description": "distinguished woman aged 62",
                "hair": "elegant gray hair",
            }
        }
        
        demo = demographics.get(demographic, demographics["women-50-60"])
        
        # Prompt for base model - plain clothing so IDM-VTON can replace it
        prompt = f"""Professional fashion catalog photography, ultra high resolution:

MODEL: {demo['description']}, {demo['hair']}, natural relaxed expression, genuine warm smile

APPEARANCE:
- Realistic facial proportions, natural features
- Soft, friendly expression
- Natural skin texture and tones
- Elegant, approachable

CLOTHING: Simple plain white t-shirt and dark neutral pants
- Basic minimal clothing (will be replaced digitally)
- Clean, plain, unremarkable

POSE & FRAMING:
- Full body shot with generous breathing room around the model
- Model positioned slightly off-center for natural feel
- Relaxed, confident stance - weight on one leg, slight hip shift
- Arms hanging naturally and loosely at sides, not rigid
- Shoulders relaxed, not stiff or squared
- One foot slightly forward for natural posture
- Looking directly at camera with genuine warmth
- Natural, comfortable body language

COMPOSITION:
- Wide framing - model takes up 60-70% of frame height, not tight crop
- Plenty of negative space around model
- Model centered vertically but slightly offset horizontally
- Room above head, space below feet
- Airy, spacious feel

BACKGROUND: 
- Pure white seamless studio backdrop
- Clean, minimal
- Even white tone, no gradients

LIGHTING:
- Professional studio lighting, soft and even
- Gentle shadows for dimension
- Natural skin rendering
- Bright but not overexposed

TECHNICAL:
- Ultra-high resolution (2K minimum)
- Sharp focus on face and upper body
- Professional fashion photography quality
- Natural color grading
- Photorealistic rendering
- Perfect facial proportions
- No compression artifacts
- Clean, crisp details"""

        print(f"🎨 Generating base model: {demographic}")
        
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )
            
            # Extract image
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        
                        if output_path:
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                            print(f"✅ Base model saved: {output_path}")
                            return output_path
                        else:
                            return image_data
            
            return None
            
        except Exception as e:
            print(f"❌ Error generating base model: {e}")
            return None
    
    def image_to_data_uri(self, file_path):
        """Convert image file to data URI"""
        try:
            import base64
            
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            data_uri = f'data:image/png;base64,{image_data}'
            print(f"  ✅ Converted to data URI ({len(data_uri)} bytes)")
            return data_uri
        except Exception as e:
            print(f"  ❌ Conversion failed: {e}")
        
        return None
    
    def apply_product_vton(self, base_model_path, product_image_url, product_description="", output_path=None):
        """
        Step 2: Use IDM-VTON to put product on the base model
        """
        print(f"🔄 Applying product with IDM-VTON...")
        print(f"  Product: {product_image_url}")
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        # Convert base model to data URI for Replicate
        if not base_model_path.startswith('http') and not base_model_path.startswith('data:'):
            print(f"  Converting base model to data URI...")
            base_model_url = self.image_to_data_uri(base_model_path)
            if not base_model_url:
                print(f"  ❌ Failed to convert base model")
                return None
        else:
            base_model_url = base_model_path
        
        # Start prediction
        payload = {
            "version": "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
            "input": {
                "human_img": base_model_url,
                "garm_img": product_image_url,
                "garment_des": product_description or "clothing item",
                "is_checked": True,
                "is_checked_crop": False,
                "denoise_steps": 30,
                "seed": 42
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 201:
            print(f"❌ Replicate API error: {response.status_code}")
            print(response.text)
            return None
        
        prediction = response.json()
        pred_id = prediction["id"]
        
        print(f"  Prediction ID: {pred_id}")
        print(f"  Processing...")
        
        # Poll for result
        start_time = time.time()
        while True:
            r = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
            p = r.json()
            status = p["status"]
            
            elapsed = int(time.time() - start_time)
            
            if status == "succeeded":
                output_url = p["output"]
                print(f"✅ Success! (took {elapsed}s)")
                
                # Download result
                if output_path:
                    img_data = requests.get(output_url).content
                    with open(output_path, 'wb') as f:
                        f.write(img_data)
                    print(f"✅ Saved: {output_path}")
                    return output_path
                else:
                    return output_url
            
            elif status == "failed":
                print(f"❌ Failed: {p.get('error', 'Unknown error')}")
                return None
            
            elif status == "canceled":
                print(f"❌ Canceled")
                return None
            
            if elapsed > 120:  # 2 minute timeout
                print(f"❌ Timeout")
                return None
            
            time.sleep(3)
    
    def generate_hybrid_photo(self, product_image_url, product_description="", demographic="women-50-60", output_dir="/tmp"):
        """
        Full two-step process:
        1. Generate base model with Gemini
        2. Apply product with IDM-VTON
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Hybrid Photo Generation")
        print(f"{'='*60}\n")
        print(f"Product: {product_image_url}")
        print(f"Demographic: {demographic}\n")
        
        # Step 1: Generate base model
        base_model_path = output_dir / f"base-model-{demographic}.png"
        base_result = self.generate_base_model(demographic, base_model_path)
        
        if not base_result:
            print("❌ Failed to generate base model")
            return None
        
        print()
        
        # Step 2: Apply product with VTON
        final_path = output_dir / f"final-{demographic}.png"
        final_result = self.apply_product_vton(
            str(base_model_path),
            product_image_url,
            product_description,
            str(final_path)
        )
        
        if not final_result:
            print("❌ Failed to apply product")
            return None
        
        print(f"\n{'='*60}")
        print(f"✅ Complete!")
        print(f"{'='*60}")
        print(f"Base model: {base_model_path}")
        print(f"Final result: {final_result}\n")
        
        return {
            "base_model": str(base_model_path),
            "final": str(final_result),
            "demographic": demographic
        }

# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid AI model photo generator")
    parser.add_argument("--product-url", required=True, help="Product image URL")
    parser.add_argument("--description", default="", help="Product description")
    parser.add_argument("--demographic", default="women-50-60", help="Target demographic")
    parser.add_argument("--output-dir", default="/tmp/hybrid-test", help="Output directory")
    
    args = parser.parse_args()
    
    generator = HybridGenerator()
    result = generator.generate_hybrid_photo(
        args.product_url,
        args.description,
        args.demographic,
        args.output_dir
    )
    
    if result:
        print(f"\n✅ Success! Check: {result['final']}")
    else:
        print(f"\n❌ Failed")
        sys.exit(1)

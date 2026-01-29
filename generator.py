#!/usr/bin/env python3
"""
AI Model Photo Generator using Banana Pro (Gemini)
Generates professional model photos from product details
"""
import os
import sys
import json
from pathlib import Path

# Install deps
try:
    from google import genai
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai"], check=True)
    from google import genai

class ModelPhotoGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-image"
    
    def load_demographics(self):
        """Load demographic templates"""
        return {
            "women-40-50": {
                "description": "elegant woman aged 45",
                "hair": "shoulder-length styled hair",
                "style": "sophisticated and professional"
            },
            "women-50-60": {
                "description": "elegant mature woman aged 55",
                "hair": "silver-gray styled hair",
                "style": "refined and confident"
            },
            "women-60-65": {
                "description": "distinguished woman aged 62",
                "hair": "elegant gray hair",
                "style": "graceful and poised"
            }
        }
    
    def generate_prompt(self, product_title, product_description="", demographic="women-50-60"):
        """
        Generate Gemini prompt from product details
        """
        demographics = self.load_demographics()
        demo = demographics.get(demographic, demographics["women-50-60"])
        
        prompt = f"""Professional fashion catalog photography:

MODEL: {demo['description']}, {demo['hair']}, {demo['style']}

PRODUCT: {product_title}
{product_description}

COMPOSITION:
- Full body shot showing entire outfit from head to feet
- Model standing in elegant, natural pose
- Clean white studio background
- Professional studio lighting with soft shadows
- Front-facing view
- Model looking directly at camera with warm, approachable expression
- Product should be the focal point and clearly visible
- High-end fashion catalog quality

STYLE:
- Photorealistic, sharp details
- Natural colors, professionally color-graded
- Clothing fits naturally on the body
- Professional retail catalog aesthetic
- Clean, minimal, elegant

REQUIREMENTS:
- Ultra-high resolution
- Sharp focus on product details
- Natural fabric draping and texture
- Realistic lighting and shadows
- Magazine-quality professional photography"""

        return prompt
    
    def generate_image(self, product_title, product_description="", demographic="women-50-60", output_path=None, product_image_url=None):
        """
        Generate AI model photo with optional product image reference
        """
        import requests
        from google import genai
        
        print(f"🎨 Generating image for: {product_title}")
        print(f"Demographic: {demographic}")
        
        # If product image URL provided, use it as visual reference
        if product_image_url:
            print(f"Using product image reference: {product_image_url}")
            
            demo = self.load_demographics().get(demographic, self.load_demographics()["women-50-60"])
            
            # Enhanced prompt for image reference
            prompt = f"""Professional fashion catalog photography - Use the provided product image as your exact visual reference.

PRODUCT IMAGE PROVIDED: Match this EXACTLY - color, pattern, texture, all details.

MODEL: {demo['description']}, {demo['hair']}, warm natural smile

POSE & FRAMING:
- Full body shot, generous space around model
- Relaxed confident stance, weight on one leg
- Arms naturally at sides, shoulders relaxed
- Looking at camera warmly
- Natural comfortable body language

COMPOSITION:
- Wide framing, model 60-70% of frame height
- Plenty of breathing room
- Slightly off-center positioning
- Airy spacious feel

BACKGROUND: Pure white seamless studio backdrop

LIGHTING: Professional studio lighting, soft and even

CLOTHING: EXACT match to reference image - same color, pattern, texture, style

TECHNICAL: Ultra-high resolution, sharp focus, natural proportions, photorealistic, professional catalog quality

CRITICAL: Match the provided product image exactly."""
            
            try:
                # Download product image
                img_data = requests.get(product_image_url).content
                
                # Generate with image reference
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        genai.types.Content(parts=[
                            genai.types.Part.from_bytes(data=img_data, mime_type="image/jpeg"),
                            genai.types.Part.from_text(text=prompt)
                        ])
                    ]
                )
            except Exception as e:
                print(f"❌ Error with image reference: {e}")
                return None
        else:
            # Fallback to text-only prompt
            prompt = self.generate_prompt(product_title, product_description, demographic)
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
            except Exception as e:
                print(f"❌ Error: {e}")
                return None
        
        # Extract image data
        try:
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        
                        if output_path:
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                            print(f"✅ Saved: {output_path}")
                            return output_path
                        else:
                            return image_data
            
            print("❌ No image generated")
            return None
            
        except Exception as e:
            print(f"❌ Error extracting image: {e}")
            return None
    
    def generate_multiple(self, product_title, product_description="", count=3, demographics=None, output_dir="/tmp"):
        """
        Generate multiple variations with different demographics
        """
        if demographics is None:
            demographics = ["women-40-50", "women-50-60", "women-60-65"]
        
        results = []
        
        for i, demo in enumerate(demographics[:count]):
            output_path = Path(output_dir) / f"model-{demo}-{i+1:02d}.png"
            
            image = self.generate_image(product_title, product_description, demo, output_path)
            
            if image:
                results.append({
                    "path": str(output_path),
                    "demographic": demo
                })
            else:
                print(f"❌ Failed to generate image {i+1}")
        
        return results

# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate AI model photos")
    parser.add_argument("--title", required=True, help="Product title")
    parser.add_argument("--description", default="", help="Product description")
    parser.add_argument("--demographic", default="women-50-60", help="Target demographic")
    parser.add_argument("--count", type=int, default=1, help="Number of images")
    parser.add_argument("--output-dir", default="/tmp", help="Output directory")
    
    args = parser.parse_args()
    
    generator = ModelPhotoGenerator()
    
    if args.count == 1:
        generator.generate_image(
            args.title,
            args.description,
            args.demographic,
            f"{args.output_dir}/model.png"
        )
    else:
        results = generator.generate_multiple(
            args.title,
            args.description,
            args.count,
            output_dir=args.output_dir
        )
        print(f"\n✅ Generated {len(results)} images")

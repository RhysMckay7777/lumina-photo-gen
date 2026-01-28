"""
Fashn.ai Product Photo Generator
Transforms product images into professional lifestyle photos with AI models.
"""

import os
import sys
import time
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

@dataclass
class GenerationResult:
    """Result of a single image generation"""
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    generation_time: float = 0.0
    api_cost: float = 0.0


class FashnGenerator:
    """
    AI Product Photo Generator using Fashn.ai API
    
    Transforms clothing product images into professional lifestyle photos
    with AI models wearing the products.
    """
    
    # API Configuration
    API_BASE_URL = "https://api.fashn.ai/v1"
    COST_PER_IMAGE = 0.075  # $0.075 per image as of March 2025
    
    def __init__(self, api_key: str, output_dir: str = "./output"):
        """
        Initialize the Fashn.ai generator
        
        Args:
            api_key: Fashn.ai API key
            output_dir: Directory to save generated images
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify API key
        if not self.api_key or self.api_key == "your_api_key_here":
            raise ValueError(
                "Invalid API key. Please set FASHN_API_KEY in .env file.\n"
                "Get your API key from: https://fashn.ai"
            )
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def generate_photo(
        self,
        garment_image_path: str,
        model_image_path: Optional[str] = None,
        category: str = "tops",
        model_type: str = "female_40_65",
        background: str = "lifestyle",
        output_name: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate a professional product photo with AI model
        
        Args:
            garment_image_path: Path to product/garment image
            model_image_path: Optional path to model image (if None, AI will generate)
            category: Product category ('tops', 'bottoms', 'dresses', 'outerwear')
            model_type: Model demographic ('female_40_65', 'female_25_40', etc.)
            background: Background type ('lifestyle', 'studio', 'outdoor')
            output_name: Custom output filename (without extension)
            
        Returns:
            GenerationResult with success status and output path
        """
        start_time = time.time()
        
        try:
            # Prepare request
            garment_image = self.encode_image(garment_image_path)
            
            payload = {
                "garment_image": garment_image,
                "category": category,
                "model_type": model_type,
                "background": background,
                "num_samples": 1  # Generate 1 image per request
            }
            
            # Add model image if provided
            if model_image_path:
                model_image = self.encode_image(model_image_path)
                payload["model_image"] = model_image
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            print(f"🎨 Generating photo for {Path(garment_image_path).name}...")
            response = requests.post(
                f"{self.API_BASE_URL}/virtual-tryon",
                json=payload,
                headers=headers,
                timeout=120
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Save generated image
            if "images" in result and len(result["images"]) > 0:
                image_data = base64.b64decode(result["images"][0])
                
                # Generate output filename
                if output_name:
                    filename = f"{output_name}.jpg"
                else:
                    garment_name = Path(garment_image_path).stem
                    timestamp = int(time.time())
                    filename = f"{garment_name}_generated_{timestamp}.jpg"
                
                output_path = self.output_dir / filename
                
                with open(output_path, "wb") as f:
                    f.write(image_data)
                
                generation_time = time.time() - start_time
                
                print(f"✅ Generated in {generation_time:.1f}s: {output_path}")
                
                return GenerationResult(
                    success=True,
                    output_path=str(output_path),
                    generation_time=generation_time,
                    api_cost=self.COST_PER_IMAGE
                )
            else:
                return GenerationResult(
                    success=False,
                    error="No images returned from API",
                    generation_time=time.time() - start_time
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text}"
            
            print(f"❌ Error: {error_msg}")
            
            return GenerationResult(
                success=False,
                error=error_msg,
                generation_time=time.time() - start_time
            )
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ Error: {error_msg}")
            
            return GenerationResult(
                success=False,
                error=error_msg,
                generation_time=time.time() - start_time
            )
    
    def batch_generate(
        self,
        garment_images: List[str],
        category: str = "tops",
        model_type: str = "female_40_65",
        background: str = "lifestyle",
        delay: float = 1.0
    ) -> List[GenerationResult]:
        """
        Generate photos for multiple products in batch
        
        Args:
            garment_images: List of paths to garment images
            category: Product category
            model_type: Model demographic
            background: Background type
            delay: Delay between requests in seconds (for rate limiting)
            
        Returns:
            List of GenerationResult objects
        """
        results = []
        total_cost = 0.0
        successful = 0
        
        print(f"\n🚀 Starting batch generation for {len(garment_images)} images...")
        print(f"📊 Settings: category={category}, model={model_type}, background={background}\n")
        
        for i, image_path in enumerate(garment_images, 1):
            print(f"[{i}/{len(garment_images)}] Processing {Path(image_path).name}")
            
            result = self.generate_photo(
                garment_image_path=image_path,
                category=category,
                model_type=model_type,
                background=background
            )
            
            results.append(result)
            
            if result.success:
                successful += 1
                total_cost += result.api_cost
            
            # Rate limiting
            if i < len(garment_images):
                time.sleep(delay)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📈 BATCH GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {successful}/{len(garment_images)}")
        print(f"❌ Failed: {len(garment_images) - successful}/{len(garment_images)}")
        print(f"💰 Total Cost: ${total_cost:.2f}")
        print(f"⏱️  Average Time: {sum(r.generation_time for r in results) / len(results):.1f}s per image")
        print(f"{'='*60}\n")
        
        return results


def main():
    """Example usage"""
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Generate professional product photos with AI models"
    )
    parser.add_argument(
        "image",
        nargs="+",
        help="Path to product image(s)"
    )
    parser.add_argument(
        "--category",
        default="tops",
        choices=["tops", "bottoms", "dresses", "outerwear"],
        help="Product category"
    )
    parser.add_argument(
        "--model",
        default="female_40_65",
        help="Model demographic (e.g., female_40_65)"
    )
    parser.add_argument(
        "--background",
        default="lifestyle",
        choices=["lifestyle", "studio", "outdoor"],
        help="Background type"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv("FASHN_API_KEY")
    if not api_key:
        print("❌ Error: FASHN_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("  FASHN_API_KEY=your_api_key_here")
        print("\nGet your API key from: https://fashn.ai")
        sys.exit(1)
    
    # Initialize generator
    generator = FashnGenerator(api_key=api_key, output_dir=args.output_dir)
    
    # Process images
    if len(args.image) == 1:
        # Single image
        result = generator.generate_photo(
            garment_image_path=args.image[0],
            category=args.category,
            model_type=args.model,
            background=args.background
        )
        
        if result.success:
            print(f"\n✅ Success! Image saved to: {result.output_path}")
            print(f"💰 Cost: ${result.api_cost:.3f}")
        else:
            print(f"\n❌ Failed: {result.error}")
            sys.exit(1)
    else:
        # Batch processing
        results = generator.batch_generate(
            garment_images=args.image,
            category=args.category,
            model_type=args.model,
            background=args.background
        )
        
        # Exit with error if all failed
        if not any(r.success for r in results):
            sys.exit(1)


if __name__ == "__main__":
    main()

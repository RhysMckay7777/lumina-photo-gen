#!/usr/bin/env python3
"""
Production Pipeline for AI Product Photo Generation
Integrates with dropship-automate scraper
"""

import os
import sys
import json
import requests
import base64
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Product from scraper"""
    id: str
    name: str
    image_url: str
    image_path: str
    category: str


@dataclass
class ModelPhoto:
    """Model/person photo for try-on"""
    id: str
    path: str
    demographic: str  # e.g., "woman_40_65"
    ethnicity: str
    pose: str


class CatVTONPipeline:
    """Production pipeline for generating product photos"""
    
    def __init__(
        self,
        catvton_url: str,
        model_photos_dir: str,
        output_dir: str
    ):
        self.catvton_url = catvton_url.rstrip('/')
        self.model_photos_dir = Path(model_photos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Load model photos
        self.model_photos = self._load_model_photos()
        logger.info(f"📸 Loaded {len(self.model_photos)} model photos")
    
    def _load_model_photos(self) -> List[ModelPhoto]:
        """Load all model photos from directory"""
        photos = []
        
        if not self.model_photos_dir.exists():
            logger.warning(f"⚠️  Model photos directory not found: {self.model_photos_dir}")
            return photos
        
        for img_path in self.model_photos_dir.glob("*.jpg"):
            # Parse filename for metadata
            # Expected format: woman_40_65_caucasian_standing_01.jpg
            parts = img_path.stem.split('_')
            
            photo = ModelPhoto(
                id=img_path.stem,
                path=str(img_path),
                demographic=f"{parts[0]}_{parts[1]}_{parts[2]}",
                ethnicity=parts[3] if len(parts) > 3 else "unknown",
                pose=parts[4] if len(parts) > 4 else "unknown"
            )
            photos.append(photo)
        
        return photos
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    
    def generate_single(
        self,
        product: Product,
        model_photo: ModelPhoto,
        output_name: str = None
    ) -> Dict:
        """Generate single try-on image"""
        
        if not output_name:
            output_name = f"{product.id}_{model_photo.id}.jpg"
        
        output_path = self.output_dir / output_name
        
        # Skip if already exists
        if output_path.exists():
            logger.info(f"⏭️  Skipping {output_name} (already exists)")
            return {
                "status": "skipped",
                "output_path": str(output_path)
            }
        
        try:
            # Encode images
            person_b64 = self._encode_image(model_photo.path)
            garment_b64 = self._encode_image(product.image_path)
            
            # Call CatVTON API
            response = requests.post(
                f"{self.catvton_url}/generate",
                json={
                    "person_image": person_b64,
                    "garment_image": garment_b64,
                    "output_format": "jpg"
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Decode and save
                image_data = base64.b64decode(result['image'])
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "result_id": result.get('result_id')
                }
            else:
                raise Exception(f"API error: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Failed {output_name}: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def generate_product_variants(
        self,
        product: Product,
        num_variants: int = 3
    ) -> List[Dict]:
        """Generate multiple variants of a product with different models"""
        
        results = []
        
        # Select diverse models
        selected_models = self.model_photos[:num_variants]
        
        for idx, model_photo in enumerate(selected_models):
            result = self.generate_single(
                product=product,
                model_photo=model_photo,
                output_name=f"{product.id}_variant{idx+1}.jpg"
            )
            results.append(result)
        
        return results
    
    def process_scraped_products(
        self,
        scraper_output_file: str,
        variants_per_product: int = 3
    ):
        """Process all products from scraper output"""
        
        # Load scraped products
        with open(scraper_output_file, 'r') as f:
            scraped_data = json.load(f)
        
        products = []
        for item in scraped_data.get('products', []):
            product = Product(
                id=item['id'],
                name=item['name'],
                image_url=item['image_url'],
                image_path=item['local_image_path'],
                category=item.get('category', 'unknown')
            )
            products.append(product)
        
        logger.info(f"📦 Processing {len(products)} products...")
        
        # Process each product
        all_results = {}
        
        for product in tqdm(products, desc="Generating variants"):
            variants = self.generate_product_variants(
                product=product,
                num_variants=variants_per_product
            )
            
            all_results[product.id] = {
                "product_name": product.name,
                "variants": variants,
                "succeeded": sum(1 for v in variants if v['status'] == 'success'),
                "failed": sum(1 for v in variants if v['status'] == 'failed')
            }
        
        # Save results manifest
        manifest_path = self.output_dir / "generation_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"✅ Processing complete!")
        logger.info(f"📊 Manifest saved to: {manifest_path}")
        
        # Summary stats
        total_variants = sum(len(r['variants']) for r in all_results.values())
        total_success = sum(r['succeeded'] for r in all_results.values())
        total_failed = sum(r['failed'] for r in all_results.values())
        
        logger.info(f"📈 Total variants: {total_variants}")
        logger.info(f"✅ Succeeded: {total_success}")
        logger.info(f"❌ Failed: {total_failed}")
        
        return all_results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Product Photo Generation Pipeline")
    parser.add_argument(
        "--catvton-url",
        required=True,
        help="CatVTON API URL (e.g., https://your-pod.runpod.net)"
    )
    parser.add_argument(
        "--model-photos",
        default="~/lumina-photo-gen/model_photos",
        help="Directory with model/person photos"
    )
    parser.add_argument(
        "--scraper-output",
        default="../dropship-automate/scraped_products.json",
        help="JSON file from scraper with product data"
    )
    parser.add_argument(
        "--output-dir",
        default="~/lumina-photo-gen/generated",
        help="Output directory for generated images"
    )
    parser.add_argument(
        "--variants",
        type=int,
        default=3,
        help="Number of variants per product"
    )
    
    args = parser.parse_args()
    
    # Expand paths
    model_photos = Path(args.model_photos).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    scraper_output = Path(args.scraper_output).expanduser()
    
    # Create pipeline
    pipeline = CatVTONPipeline(
        catvton_url=args.catvton_url,
        model_photos_dir=str(model_photos),
        output_dir=str(output_dir)
    )
    
    # Process products
    results = pipeline.process_scraped_products(
        scraper_output_file=str(scraper_output),
        variants_per_product=args.variants
    )


if __name__ == "__main__":
    main()

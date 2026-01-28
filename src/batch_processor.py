"""
Batch Processor for Product Photo Generation
Integrates with dropship-automate scraper and processes products in bulk.
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from tqdm import tqdm

from fashn_generator import FashnGenerator, GenerationResult


@dataclass
class ProductImage:
    """Represents a product to be processed"""
    product_id: str
    image_url: str
    local_path: Optional[str] = None
    category: str = "tops"
    title: Optional[str] = None
    source: str = "aliexpress"
    
    
@dataclass
class ProcessingReport:
    """Report of batch processing results"""
    total_products: int
    successful: int
    failed: int
    total_cost: float
    total_time: float
    timestamp: str
    results: List[Dict[str, Any]]
    

class BatchProcessor:
    """
    Batch processor for generating product photos at scale
    """
    
    def __init__(
        self,
        api_key: str,
        output_dir: str = "./output",
        download_dir: str = "./downloads",
        max_concurrent: int = 3
    ):
        """
        Initialize batch processor
        
        Args:
            api_key: Fashn.ai API key
            output_dir: Directory for generated images
            download_dir: Directory for downloaded source images
            max_concurrent: Maximum concurrent API requests
        """
        self.generator = FashnGenerator(api_key=api_key, output_dir=output_dir)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def download_image(
        self,
        session: aiohttp.ClientSession,
        url: str,
        output_path: Path
    ) -> bool:
        """
        Download image from URL
        
        Args:
            session: aiohttp session
            url: Image URL
            output_path: Where to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        f.write(await response.read())
                    return True
                else:
                    self.logger.error(f"Failed to download {url}: HTTP {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return False
    
    async def download_products(self, products: List[ProductImage]) -> List[ProductImage]:
        """
        Download all product images concurrently
        
        Args:
            products: List of ProductImage objects
            
        Returns:
            Updated list with local_path set
        """
        self.logger.info(f"📥 Downloading {len(products)} product images...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for product in products:
                # Generate local filename
                filename = f"{product.product_id}.jpg"
                local_path = self.download_dir / filename
                
                # Skip if already downloaded
                if local_path.exists():
                    product.local_path = str(local_path)
                    self.logger.info(f"✓ Already downloaded: {filename}")
                    continue
                
                # Create download task
                task = self.download_image(session, product.image_url, local_path)
                tasks.append((product, local_path, task))
            
            # Download concurrently with progress bar
            if tasks:
                with tqdm(total=len(tasks), desc="Downloading") as pbar:
                    for product, local_path, task in tasks:
                        success = await task
                        if success:
                            product.local_path = str(local_path)
                            self.logger.info(f"✓ Downloaded: {product.product_id}")
                        else:
                            self.logger.error(f"✗ Failed: {product.product_id}")
                        pbar.update(1)
        
        # Filter out products that failed to download
        successful = [p for p in products if p.local_path is not None]
        self.logger.info(f"✅ Downloaded {len(successful)}/{len(products)} images")
        
        return successful
    
    def process_batch(
        self,
        products: List[ProductImage],
        model_type: str = "female_40_65",
        background: str = "lifestyle",
        delay: float = 1.0
    ) -> ProcessingReport:
        """
        Process a batch of products
        
        Args:
            products: List of ProductImage objects
            model_type: AI model demographic
            background: Background type
            delay: Delay between API calls
            
        Returns:
            ProcessingReport with results
        """
        start_time = datetime.now()
        results = []
        successful = 0
        failed = 0
        total_cost = 0.0
        
        self.logger.info(f"\n🚀 Starting batch processing of {len(products)} products")
        self.logger.info(f"📊 Settings: model={model_type}, background={background}\n")
        
        for i, product in enumerate(products, 1):
            self.logger.info(f"[{i}/{len(products)}] Processing product {product.product_id}")
            
            # Generate output filename
            output_name = f"{product.product_id}_generated"
            
            # Generate photo
            result = self.generator.generate_photo(
                garment_image_path=product.local_path,
                category=product.category,
                model_type=model_type,
                background=background,
                output_name=output_name
            )
            
            # Record result
            result_dict = {
                "product_id": product.product_id,
                "title": product.title,
                "category": product.category,
                "source_image": product.image_url,
                "success": result.success,
                "output_path": result.output_path,
                "error": result.error,
                "generation_time": result.generation_time,
                "cost": result.api_cost
            }
            results.append(result_dict)
            
            if result.success:
                successful += 1
                total_cost += result.api_cost
            else:
                failed += 1
            
            # Rate limiting
            if i < len(products):
                asyncio.sleep(delay)
        
        # Calculate total time
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Create report
        report = ProcessingReport(
            total_products=len(products),
            successful=successful,
            failed=failed,
            total_cost=total_cost,
            total_time=total_time,
            timestamp=datetime.now().isoformat(),
            results=results
        )
        
        # Save report
        self._save_report(report)
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _save_report(self, report: ProcessingReport):
        """Save processing report to JSON"""
        report_path = Path("reports") / f"batch_report_{int(datetime.now().timestamp())}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        
        self.logger.info(f"📄 Report saved to: {report_path}")
    
    def _print_summary(self, report: ProcessingReport):
        """Print processing summary"""
        print(f"\n{'='*60}")
        print(f"📈 BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {report.successful}/{report.total_products}")
        print(f"❌ Failed: {report.failed}/{report.total_products}")
        print(f"💰 Total Cost: ${report.total_cost:.2f}")
        print(f"⏱️  Total Time: {report.total_time:.1f}s")
        print(f"⏱️  Avg Time: {report.total_time/report.total_products:.1f}s per image")
        print(f"📊 Success Rate: {(report.successful/report.total_products)*100:.1f}%")
        print(f"{'='*60}\n")
    
    def process_from_json(self, json_path: str, **kwargs) -> ProcessingReport:
        """
        Process products from a JSON file (e.g., from dropship-automate scraper)
        
        Args:
            json_path: Path to JSON file with product data
            **kwargs: Additional arguments for process_batch
            
        Returns:
            ProcessingReport
            
        Expected JSON format:
        {
            "products": [
                {
                    "id": "product_123",
                    "image_url": "https://...",
                    "title": "Women's Dress",
                    "category": "dresses"
                },
                ...
            ]
        }
        """
        self.logger.info(f"📂 Loading products from {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Convert to ProductImage objects
        products = []
        for item in data.get("products", []):
            product = ProductImage(
                product_id=item.get("id", str(len(products))),
                image_url=item["image_url"],
                category=item.get("category", "tops"),
                title=item.get("title"),
                source=item.get("source", "aliexpress")
            )
            products.append(product)
        
        self.logger.info(f"✅ Loaded {len(products)} products")
        
        # Download images
        downloaded = asyncio.run(self.download_products(products))
        
        # Process batch
        return self.process_batch(downloaded, **kwargs)


def main():
    """Example usage"""
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Batch process product images"
    )
    parser.add_argument(
        "input",
        help="Path to JSON file with product data"
    )
    parser.add_argument(
        "--model",
        default="female_40_65",
        help="Model demographic"
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
    parser.add_argument(
        "--download-dir",
        default="./downloads",
        help="Download directory"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent downloads"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv("FASHN_API_KEY")
    if not api_key:
        print("❌ Error: FASHN_API_KEY not found")
        return 1
    
    # Initialize processor
    processor = BatchProcessor(
        api_key=api_key,
        output_dir=args.output_dir,
        download_dir=args.download_dir,
        max_concurrent=args.max_concurrent
    )
    
    # Process batch
    try:
        report = processor.process_from_json(
            args.input,
            model_type=args.model,
            background=args.background
        )
        
        # Exit with error if all failed
        if report.successful == 0:
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

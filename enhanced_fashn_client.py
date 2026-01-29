#!/usr/bin/env python3
"""
Enhanced Fashn.ai client with error handling, retries, and model rotation
"""
import requests
import base64
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FashnClient:
    """Production-ready Fashn.ai client with resilience features"""
    
    def __init__(self, api_key: str, model_photos_dir: str = "model_photos_new"):
        self.api_key = api_key
        self.model_photos_dir = Path(model_photos_dir)
        self.base_url = "https://api.fashn.ai/v1"
        
        # Load working models
        self.working_models = self._load_working_models()
        self.current_model_index = 0
        
        # Stats tracking
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "retries": 0,
            "model_rotations": 0,
            "total_cost": 0.0
        }
    
    def _load_working_models(self) -> List[Path]:
        """Load list of working model photos"""
        results_file = Path("model_test_results.json")
        
        if results_file.exists():
            with open(results_file) as f:
                data = json.load(f)
                working_names = data.get("working", [])
                
                if working_names:
                    models = [self.model_photos_dir / name for name in working_names]
                    logger.info(f"✅ Loaded {len(models)} working models")
                    return models
        
        # Fallback: use all models in directory
        models = sorted(list(self.model_photos_dir.glob("*.jpg")))
        logger.warning(f"⚠️  No test results found, using all {len(models)} models")
        return models
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _get_next_model(self) -> Optional[Path]:
        """Get next model photo (rotation)"""
        if not self.working_models:
            return None
        
        model = self.working_models[self.current_model_index]
        self.current_model_index = (self.current_model_index + 1) % len(self.working_models)
        
        if self.current_model_index == 0:
            self.stats["model_rotations"] += 1
        
        return model
    
    def _make_request(self, garment_path: str, model_path: str, 
                     category: str = "tops", num_samples: int = 1) -> Dict:
        """Make API request with proper error handling"""
        
        garment_b64 = self._encode_image(garment_path)
        model_b64 = self._encode_image(model_path)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model_name": "tryon-v1.6",
            "inputs": {
                "category": category,
                "garment_image": f"data:image/jpeg;base64,{garment_b64}",
                "model_image": f"data:image/jpeg;base64,{model_b64}",
                "num_samples": num_samples
            }
        }
        
        response = requests.post(
            f"{self.base_url}/run",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def _poll_job(self, job_id: str, max_wait: int = 120) -> Dict:
        """Poll for job completion"""
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{self.base_url}/status/{job_id}",
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            status = result.get('status')
            
            if status == 'succeeded':
                return result
            elif status == 'failed':
                raise Exception(f"Job failed: {result.get('error')}")
            
            time.sleep(2)
        
        raise TimeoutError(f"Job {job_id} timed out after {max_wait}s")
    
    def generate(self, garment_path: str, output_path: str, 
                category: str = "tops", max_retries: int = 3) -> bool:
        """
        Generate virtual try-on with automatic retries and model rotation
        
        Returns: True if successful, False otherwise
        """
        
        self.stats["total_requests"] += 1
        
        for attempt in range(max_retries):
            try:
                # Get model photo
                model_path = self._get_next_model()
                
                if not model_path:
                    logger.error("❌ No model photos available")
                    return False
                
                if attempt > 0:
                    self.stats["retries"] += 1
                    logger.info(f"🔄 Retry {attempt}/{max_retries} with model: {model_path.name}")
                else:
                    logger.info(f"🎨 Generating with model: {model_path.name}")
                
                # Make request
                result = self._make_request(garment_path, str(model_path), category)
                
                # Check for job ID
                job_id = result.get('id')
                if not job_id:
                    raise Exception("No job ID in response")
                
                # Poll for completion
                logger.info(f"⏳ Waiting for job {job_id}...")
                final_result = self._poll_job(job_id)
                
                # Extract and save output
                if 'output' not in final_result or not final_result['output']:
                    raise Exception("No output in result")
                
                output_b64 = final_result['output'][0]
                if ',' in output_b64:
                    output_b64 = output_b64.split(',')[1]
                
                output_data = base64.b64decode(output_b64)
                
                with open(output_path, 'wb') as f:
                    f.write(output_data)
                
                # Update stats
                self.stats["successful"] += 1
                self.stats["total_cost"] += 0.04  # ~$40 per 1000 = $0.04 per image
                
                logger.info(f"✅ Saved: {output_path}")
                return True
            
            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt + 1} failed: {str(e)[:100]}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"   Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries} attempts failed")
                    self.stats["failed"] += 1
                    return False
        
        return False
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "avg_cost_per_image": (
                self.stats["total_cost"] / self.stats["successful"]
                if self.stats["successful"] > 0 else 0
            )
        }
    
    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("📊 FASHN.AI USAGE STATISTICS")
        print("=" * 60)
        print(f"Total Requests:    {stats['total_requests']}")
        print(f"Successful:        {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"Failed:            {stats['failed']}")
        print(f"Retries:           {stats['retries']}")
        print(f"Model Rotations:   {stats['model_rotations']}")
        print(f"Total Cost:        ${stats['total_cost']:.2f}")
        print(f"Avg Cost/Image:    ${stats['avg_cost_per_image']:.4f}")
        print("=" * 60 + "\n")


# Example usage
if __name__ == "__main__":
    import sys
    
    API_KEY = "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD"
    
    client = FashnClient(API_KEY)
    
    garment = sys.argv[1] if len(sys.argv) > 1 else "test_product.jpg"
    output = sys.argv[2] if len(sys.argv) > 2 else "output_enhanced.jpg"
    
    success = client.generate(garment, output)
    
    client.print_stats()
    
    if success:
        print(f"✅ Success! Check {output}")
    else:
        print(f"❌ Generation failed after all retries")

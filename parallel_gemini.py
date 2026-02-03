"""
Parallel Gemini Image Processor - Tiered Rate Limiting

Architecture:
- Each key has its own rate limiter based on tier
- Tier 1: 10 IPM (6 second interval)
- Free tier: 2 IPM (30 second interval)
- Round-robin key selection with independent rate limiting

Your setup:
- 5 Tier 1 keys: 50 IPM
- 5 Free keys: 10 IPM
- TOTAL: 60 IPM
"""

import asyncio
import base64
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Callable, Any
import httpx

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from config import GeminiKeyConfig, PROCESSING_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parallel.gemini")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ImageTask:
    """A single image generation task"""
    product_id: str
    product_title: str
    product_description: str
    image_url: str  # Reference image URL (empty for text-only)
    image_index: int  # 0, 1, 2 for 3 images per product
    image_bytes: Optional[bytes] = None


@dataclass
class EnhancedImage:
    """Result of image enhancement"""
    product_id: str
    product_title: str
    image_index: int
    success: bool = False
    enhanced_bytes: Optional[bytes] = None
    mime_type: str = "image/png"
    error: Optional[str] = None
    key_name: str = ""
    generation_time: float = 0.0


# =============================================================================
# KEY RATE LIMITER
# =============================================================================

@dataclass
class KeyRateLimiter:
    """Rate limiter for a single API key with tier-aware intervals"""
    key_name: str
    tier: str
    ipm_limit: int
    min_interval: float = field(init=False)  # Seconds between requests
    last_request_time: float = 0.0
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_wait_time: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def __post_init__(self):
        # Calculate interval with 1 second safety buffer
        self.min_interval = (60.0 / self.ipm_limit) + 1.0
        logger.debug(f"{self.key_name}: {self.ipm_limit} IPM, {self.min_interval:.1f}s interval")
    
    async def acquire(self) -> float:
        """Wait for rate limit. Returns actual wait time in seconds."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = 0.0
            
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()
            self.total_wait_time += wait_time
            return wait_time
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0.0


# =============================================================================
# GEMINI KEY WORKER
# =============================================================================

@dataclass
class GeminiKeyWorker:
    """A worker with its own API key, client, and rate limiter"""
    config: GeminiKeyConfig
    client: Any = field(init=False)
    rate_limiter: KeyRateLimiter = field(init=False)
    
    def __post_init__(self):
        if genai is None:
            raise ImportError("google-genai not installed!")
        
        # Initialize client with this key
        self.client = genai.Client(api_key=self.config.api_key)
        
        # Initialize rate limiter
        self.rate_limiter = KeyRateLimiter(
            key_name=self.config.key_name,
            tier=self.config.tier,
            ipm_limit=self.config.ipm_limit
        )
    
    @property
    def key_name(self) -> str:
        return self.config.key_name
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "key_name": self.config.key_name,
            "tier": self.config.tier,
            "ipm_limit": self.config.ipm_limit,
            "requests": self.rate_limiter.request_count,
            "success": self.rate_limiter.success_count,
            "failures": self.rate_limiter.failure_count,
            "success_rate": self.rate_limiter.success_rate,
            "wait_time": self.rate_limiter.total_wait_time
        }


# =============================================================================
# PARALLEL GEMINI PROCESSOR
# =============================================================================

class ParallelGeminiProcessor:
    """
    Parallel image processor with tiered rate limiting.
    
    Features:
    - Independent rate limiting per key based on tier
    - Round-robin key selection
    - Text-only generation when no reference image
    - Detailed per-key statistics
    """
    
    def __init__(self, key_configs: List[GeminiKeyConfig]):
        self.model = PROCESSING_CONFIG["gemini_model"]
        self.workers: List[GeminiKeyWorker] = []
        
        # Initialize workers
        for config in key_configs:
            if config.api_key:
                try:
                    worker = GeminiKeyWorker(config=config)
                    self.workers.append(worker)
                    logger.info(f"✅ Initialized {config.key_name}: {config.ipm_limit} IPM")
                except Exception as e:
                    logger.error(f"❌ Failed to init {config.key_name}: {e}")
        
        if not self.workers:
            raise ValueError("No valid Gemini API keys!")
        
        # Queue for round-robin selection
        self._worker_queue: asyncio.Queue = asyncio.Queue()
        self._queue_initialized = False
        
        # Calculate capacities
        self.total_ipm = sum(w.config.ipm_limit for w in self.workers)
        tier1_ipm = sum(w.config.ipm_limit for w in self.workers if w.config.tier == "tier1")
        free_ipm = sum(w.config.ipm_limit for w in self.workers if w.config.tier == "free")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("🚀 Gemini Processor Ready")
        logger.info(f"   {len(self.workers)} keys | {self.total_ipm} IPM capacity")
        logger.info("=" * 60)
    
    async def _init_queue(self):
        """Initialize worker queue (called once)"""
        if not self._queue_initialized:
            for i in range(len(self.workers)):
                await self._worker_queue.put(i)
            self._queue_initialized = True
    
    async def _get_worker(self) -> tuple[int, GeminiKeyWorker]:
        """Get next available worker (round-robin)"""
        await self._init_queue()
        idx = await self._worker_queue.get()
        return idx, self.workers[idx]
    
    async def _release_worker(self, idx: int):
        """Return worker to queue"""
        await self._worker_queue.put(idx)
    
    def _build_prompt(self, task: ImageTask, has_reference_image: bool = False) -> str:
        """
        Build category-aware prompt using CJ category system.
        This dramatically improves generation success rate.
        """
        # Import category system (lazy to avoid circular imports)
        try:
            from cj_category_system import detect_category
            from cj_prompts import build_prompt
            
            # Create product dict for category detection
            product = {
                'title': task.product_title,
                'description': task.product_description or '',
                'tags': []
            }
            
            # Detect category
            category_result = detect_category(product)
            
            # Build optimized prompt
            base_prompt = build_prompt(product, category_result)
            
            # Add reference image instruction if we have one
            if has_reference_image:
                return f"""Using the provided reference image as a guide, {base_prompt.lower()}

IMPORTANT: Use the reference image to understand the product's appearance, colors, and details. Generate a NEW professional photograph based on this, not a copy."""
            else:
                return base_prompt
                
        except ImportError:
            # Fallback if category system not available
            return self._build_fallback_prompt(task, has_reference_image)
    
    def _build_fallback_prompt(self, task: ImageTask, has_reference_image: bool = False) -> str:
        """Fallback prompt if category system unavailable"""
        if has_reference_image:
            return f"""Transform this product image into a professional e-commerce photograph.

Product: {task.product_title}

Requirements:
1. Professional studio photography
2. Clean white or gradient background
3. Sharp focus and professional lighting
4. E-commerce catalog quality
5. Keep product authentic

Generate a professional product photograph."""
        else:
            return f"""Create a professional e-commerce product photograph.

Product: {task.product_title}
Description: {(task.product_description or "")[:200]}

Requirements:
1. Photorealistic, commercial-quality image
2. Clean professional background
3. No text, watermarks, or logos
4. High resolution and sharp detail
5. Professional studio lighting

Generate the product photograph."""
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        if not url:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=PROCESSING_CONFIG["download_timeout"]) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.content
        except Exception as e:
            logger.warning(f"Download failed: {str(e)[:50]}")
        
        return None
    
    async def _generate_image(self, worker: GeminiKeyWorker, task: ImageTask) -> EnhancedImage:
        """Generate image using specific worker"""
        start_time = time.time()
        
        result = EnhancedImage(
            product_id=task.product_id,
            product_title=task.product_title,
            image_index=task.image_index,
            key_name=worker.key_name
        )
        
        try:
            # Wait for rate limit
            wait_time = await worker.rate_limiter.acquire()
            worker.rate_limiter.request_count += 1
            
            if wait_time > 0.5:
                logger.debug(f"   [{worker.key_name}] Waited {wait_time:.1f}s")
            
            # Build request contents
            contents = []
            has_reference = bool(task.image_bytes)
            
            # Add reference image if available
            if task.image_bytes:
                contents.append(types.Part.from_bytes(
                    data=task.image_bytes,
                    mime_type="image/jpeg"
                ))
            
            # Add prompt (category-aware)
            prompt = self._build_prompt(task, has_reference_image=has_reference)
            contents.append(types.Part.from_text(text=prompt))
            
            # Generate with Gemini
            response = await worker.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_modalities=["IMAGE", "TEXT"]
                )
            )
            
            # Extract generated image
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Check inline_data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data') and part.inline_data.data:
                            result.success = True
                            result.enhanced_bytes = part.inline_data.data
                            result.mime_type = getattr(part.inline_data, 'mime_type', 'image/png')
                            worker.rate_limiter.success_count += 1
                            break
            
            if not result.success:
                result.error = "No image in response (content policy)"
                worker.rate_limiter.failure_count += 1
        
        except Exception as e:
            error_msg = str(e)
            result.error = error_msg[:100]
            worker.rate_limiter.failure_count += 1
            
            # Extra backoff on rate limit errors
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"   [{worker.key_name}] Rate limit! Extra 10s backoff...")
                await asyncio.sleep(10)
        
        result.generation_time = time.time() - start_time
        return result
    
    async def enhance_batch(
        self,
        tasks: List[ImageTask],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[EnhancedImage]:
        """
        Process batch of image tasks using all workers in parallel.
        
        Args:
            tasks: List of ImageTask objects
            progress_callback: Optional callback(completed, total, current_title)
        
        Returns:
            List of EnhancedImage results
        """
        total = len(tasks)
        if total == 0:
            return []
        
        logger.info(f"🎨 Generating {total} images (est. {total / self.total_ipm:.1f} min)...")
        
        start_time = time.time()
        completed = 0
        results: List[EnhancedImage] = []
        
        # Semaphore limits concurrent tasks to number of workers
        semaphore = asyncio.Semaphore(len(self.workers))
        
        async def process_one(task: ImageTask) -> EnhancedImage:
            nonlocal completed
            
            async with semaphore:
                idx, worker = await self._get_worker()
                
                try:
                    # Download reference image if URL provided
                    if task.image_url and not task.image_bytes:
                        task.image_bytes = await self._download_image(task.image_url)
                    
                    # Generate image
                    result = await self._generate_image(worker, task)
                    
                    # Only log failures
                    completed += 1
                    if not result.success:
                        logger.warning(f"   ⚠️ FAILED: {task.product_title[:40]} - {result.error or 'No image generated'}")
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(completed, total, task.product_title)
                    
                    return result
                
                finally:
                    await self._release_worker(idx)
        
        # Process all tasks concurrently
        task_coroutines = [process_one(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(EnhancedImage(
                    product_id=tasks[i].product_id,
                    product_title=tasks[i].product_title,
                    image_index=tasks[i].image_index,
                    success=False,
                    error=str(result)[:100]
                ))
            else:
                final_results.append(result)
        
        # Log summary only
        elapsed = time.time() - start_time
        success_count = sum(1 for r in final_results if r.success)
        fail_count = total - success_count
        
        logger.info(f"📊 Generation complete: {success_count}/{total} success | {elapsed:.0f}s | {success_count / (elapsed/60):.1f} img/min")
        if fail_count > 0:
            logger.warning(f"   ⚠️ {fail_count} images failed")
        
        return final_results


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_processor(key_configs: List[GeminiKeyConfig]) -> ParallelGeminiProcessor:
    """Create a parallel processor with the given key configs"""
    return ParallelGeminiProcessor(key_configs)


def load_api_keys_from_env() -> List[str]:
    """Legacy function - load API keys as list of strings"""
    from config import GEMINI_KEYS
    return [k.api_key for k in GEMINI_KEYS]

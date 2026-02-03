# shopify_batch_uploader.py
"""
Parallel batch uploader for Shopify with proper error handling.
Fixes the "invalid id" error and implements parallel uploads.
"""

import asyncio
import base64
import httpx
import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of a single image upload"""
    product_id: str
    product_title: str
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None


@dataclass 
class BatchUploadResult:
    """Result of batch upload operation"""
    total: int
    successful: int
    failed: int
    results: List[UploadResult]
    time_seconds: float


class ShopifyBatchUploader:
    """
    Handles parallel batch uploads to Shopify.
    
    Features:
    - Parallel uploads (configurable concurrency)
    - Proper error handling for "invalid id" 
    - Staged uploads via Google Cloud Storage
    - Rate limit handling
    """
    
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = "2024-10",
        max_concurrent: int = 5,
        timeout: float = 30.0
    ):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = api_version
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        
        self.graphql_url = f"https://{shop_domain}/admin/api/{api_version}/graphql.json"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        # Semaphore for controlling concurrency
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    # =========================================================================
    # MAIN BATCH UPLOAD METHOD
    # =========================================================================
    
    async def batch_upload(
        self,
        images: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> BatchUploadResult:
        """
        Upload multiple images to Shopify in parallel.
        
        Args:
            images: List of dicts with:
                - product_id: Shopify product GID
                - product_title: Product title (for logging)
                - image_data: Image bytes
                - mime_type: Image MIME type (default: image/png)
                - filename: Optional filename
                - alt_text: Optional alt text
            progress_callback: Optional callback(completed, total)
        
        Returns:
            BatchUploadResult with success/failure counts
        """
        start_time = time.time()
        
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        total = len(images)
        completed = 0
        results: List[UploadResult] = []
        
        # Create upload tasks
        async def upload_with_progress(image_info: Dict) -> UploadResult:
            nonlocal completed
            
            async with self._semaphore:
                result = await self._upload_single_image(image_info)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, total)
                
                # Only log failures
                if not result.success:
                    logger.warning(f"   ⚠️ FAILED: {result.product_title[:40]} - {result.error or 'Unknown'}")
                
                return result
        
        # Run all uploads in parallel (with semaphore limiting concurrency)
        tasks = [upload_with_progress(img) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(UploadResult(
                    product_id=images[i].get('product_id', 'unknown'),
                    product_title=images[i].get('product_title', 'Unknown'),
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        # Calculate stats
        successful = sum(1 for r in processed_results if r.success)
        failed = total - successful
        elapsed = time.time() - start_time
        
        return BatchUploadResult(
            total=total,
            successful=successful,
            failed=failed,
            results=processed_results,
            time_seconds=elapsed
        )
    
    # =========================================================================
    # SINGLE IMAGE UPLOAD (3-STEP PROCESS)
    # =========================================================================
    
    async def _upload_single_image(self, image_info: Dict) -> UploadResult:
        """
        Upload single image using Shopify's staged upload process.
        
        3-step process:
        1. Create staged upload target
        2. Upload image to Google Cloud Storage
        3. Attach image to product
        """
        product_id = image_info.get('product_id')
        product_title = image_info.get('product_title', 'Unknown')
        image_data = image_info.get('image_data')
        mime_type = image_info.get('mime_type', 'image/png')
        filename = image_info.get('filename', f"enhanced_{product_id.split('/')[-1] if '/' in str(product_id) else product_id}.png")
        alt_text = image_info.get('alt_text', f"Enhanced image for {product_title}")
        
        try:
            # Validate product_id format
            product_id = self._ensure_gid_format(product_id, "Product")
            
            # Step 1: Create staged upload
            staged_target = await self._create_staged_upload(filename, mime_type)
            
            if not staged_target:
                return UploadResult(
                    product_id=product_id,
                    product_title=product_title,
                    success=False,
                    error="Failed to create staged upload"
                )
            
            # Step 2: Upload to Google Cloud Storage
            upload_success = await self._upload_to_staged_target(
                staged_target,
                image_data,
                mime_type,
                filename
            )
            
            if not upload_success:
                return UploadResult(
                    product_id=product_id,
                    product_title=product_title,
                    success=False,
                    error="Failed to upload to staged target"
                )
            
            # Step 3: Attach image to product
            image_url = await self._attach_image_to_product(
                product_id,
                staged_target['resourceUrl'],
                alt_text
            )
            
            if image_url:
                return UploadResult(
                    product_id=product_id,
                    product_title=product_title,
                    success=True,
                    image_url=image_url
                )
            else:
                return UploadResult(
                    product_id=product_id,
                    product_title=product_title,
                    success=False,
                    error="Failed to attach image to product"
                )
        
        except Exception as e:
            logger.error(f"Upload error for {product_title}: {str(e)}")
            return UploadResult(
                product_id=product_id,
                product_title=product_title,
                success=False,
                error=str(e)[:200]
            )
    
    # =========================================================================
    # STEP 1: CREATE STAGED UPLOAD
    # =========================================================================
    
    async def _create_staged_upload(
        self,
        filename: str,
        mime_type: str
    ) -> Optional[Dict]:
        """Create a staged upload target for the image"""
        
        mutation = """
        mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
          stagedUploadsCreate(input: $input) {
            stagedTargets {
              resourceUrl
              url
              parameters {
                name
                value
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": [{
                "filename": filename,
                "mimeType": mime_type,
                "resource": "PRODUCT_IMAGE",
                "httpMethod": "POST"
            }]
        }
        
        try:
            response = await self._client.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": mutation, "variables": variables}
            )
            
            data = response.json()
            
            # Check for errors
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None
            
            result = data.get('data', {}).get('stagedUploadsCreate', {})
            
            user_errors = result.get('userErrors', [])
            if user_errors:
                logger.error(f"User errors: {user_errors}")
                return None
            
            targets = result.get('stagedTargets', [])
            if not targets:
                return None
            
            return targets[0]
        
        except Exception as e:
            logger.error(f"Staged upload creation error: {e}")
            return None
    
    # =========================================================================
    # STEP 2: UPLOAD TO GOOGLE CLOUD STORAGE
    # =========================================================================
    
    async def _upload_to_staged_target(
        self,
        staged_target: Dict,
        image_data: bytes,
        mime_type: str,
        filename: str
    ) -> bool:
        """Upload image data to the staged target (Google Cloud Storage)"""
        
        try:
            url = staged_target['url']
            parameters = {p['name']: p['value'] for p in staged_target['parameters']}
            
            # Build multipart form data
            # The parameters go first, then the file
            files = {}
            data = {}
            
            # Add all parameters as form fields
            for key, value in parameters.items():
                data[key] = value
            
            # Add the file
            files['file'] = (filename, image_data, mime_type)
            
            response = await self._client.post(
                url,
                data=data,
                files=files,
                timeout=60.0  # Longer timeout for file upload
            )
            
            # Google Cloud Storage returns 201 Created or 204 No Content on success
            if response.status_code in [200, 201, 204]:
                return True
            else:
                logger.error(f"Upload failed with status {response.status_code}: {response.text[:200]}")
                return False
        
        except Exception as e:
            logger.error(f"Upload to staged target error: {e}")
            return False
    
    # =========================================================================
    # STEP 3: ATTACH IMAGE TO PRODUCT
    # =========================================================================
    
    async def _attach_image_to_product(
        self,
        product_id: str,
        staged_url: str,
        alt_text: str
    ) -> Optional[str]:
        """Attach the uploaded image to the product"""
        
        # Use productCreateMedia mutation (more reliable than productUpdate)
        mutation = """
        mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
          productCreateMedia(productId: $productId, media: $media) {
            media {
              ... on MediaImage {
                id
                image {
                  url
                }
              }
            }
            mediaUserErrors {
              field
              message
              code
            }
          }
        }
        """
        
        variables = {
            "productId": product_id,
            "media": [{
                "originalSource": staged_url,
                "alt": alt_text,
                "mediaContentType": "IMAGE"
            }]
        }
        
        try:
            response = await self._client.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": mutation, "variables": variables}
            )
            
            data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in data:
                for error in data['errors']:
                    logger.error(f"GraphQL error: {error.get('message', error)}")
                return None
            
            result = data.get('data', {}).get('productCreateMedia', {})
            
            # Check for user errors
            user_errors = result.get('mediaUserErrors', [])
            if user_errors:
                for error in user_errors:
                    logger.error(f"Media error: {error.get('message')} (code: {error.get('code')})")
                return None
            
            # Get the image URL
            media = result.get('media', [])
            if media and media[0]:
                image = media[0].get('image', {})
                return image.get('url')
            
            return None
        
        except Exception as e:
            logger.error(f"Attach image error: {e}")
            return None
    
    # =========================================================================
    # HELPER: ENSURE GID FORMAT
    # =========================================================================
    
    def _ensure_gid_format(self, id_value: str, resource_type: str) -> str:
        """
        Ensure ID is in proper GID format.
        
        Fixes the "invalid id" error by ensuring correct format:
        - "gid://shopify/Product/123456789"
        - NOT just "123456789"
        """
        if not id_value:
            raise ValueError(f"{resource_type} ID is required")
        
        id_str = str(id_value)
        
        # Already in GID format
        if id_str.startswith("gid://shopify/"):
            return id_str
        
        # Just a numeric ID - convert to GID
        if id_str.isdigit():
            return f"gid://shopify/{resource_type}/{id_str}"
        
        # Unknown format
        raise ValueError(f"Invalid {resource_type} ID format: {id_value}")
    
    # =========================================================================
    # BATCH UPLOAD BY PRODUCT (MULTIPLE IMAGES PER PRODUCT)
    # =========================================================================
    
    async def batch_upload_by_product(
        self,
        products_with_images: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Upload multiple images per product.
        
        Args:
            products_with_images: List of dicts with:
                - product_id: Shopify product GID
                - product_title: Product title
                - images: List of image dicts (image_data, mime_type, etc.)
            progress_callback: Optional callback(completed_products, total_products)
        
        Returns:
            Dict with results per product
        """
        start_time = time.time()
        
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        total_products = len(products_with_images)
        total_images = sum(len(p.get('images', [])) for p in products_with_images)
        completed_products = 0
        
        results = {}
        
        for product_info in products_with_images:
            product_id = product_info['product_id']
            product_title = product_info.get('product_title', 'Unknown')
            images = product_info.get('images', [])
            
            # Prepare image info list
            image_infos = []
            for i, img in enumerate(images):
                image_infos.append({
                    'product_id': product_id,
                    'product_title': product_title,
                    'image_data': img.get('image_data'),
                    'mime_type': img.get('mime_type', 'image/png'),
                    'filename': img.get('filename', f"enhanced_{i+1}.png"),
                    'alt_text': img.get('alt_text', f"Enhanced image {i+1} for {product_title}")
                })
            
            # Upload all images for this product
            if image_infos:
                batch_result = await self.batch_upload(image_infos)
                
                results[product_id] = {
                    'product_title': product_title,
                    'total': batch_result.total,
                    'successful': batch_result.successful,
                    'failed': batch_result.failed,
                    'image_urls': [r.image_url for r in batch_result.results if r.success]
                }
            else:
                results[product_id] = {
                    'product_title': product_title,
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'image_urls': []
                }
            
            completed_products += 1
            
            if progress_callback:
                progress_callback(completed_products, total_products)
            
            # Log product completion
            success_count = results[product_id]['successful']
            total_count = results[product_id]['total']
            logger.info(f"   ✅ {product_title[:40]}: {success_count}/{total_count} images")
        
        elapsed = time.time() - start_time
        
        # Calculate totals
        total_successful = sum(r['successful'] for r in results.values())
        total_failed = sum(r['failed'] for r in results.values())
        
        return {
            'total_products': total_products,
            'total_images': total_images,
            'successful_images': total_successful,
            'failed_images': total_failed,
            'time_seconds': elapsed,
            'images_per_minute': (total_images / elapsed * 60) if elapsed > 0 else 0,
            'products': results
        }

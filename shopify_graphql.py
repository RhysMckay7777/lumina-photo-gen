"""
Shopify GraphQL Client for Photo Enhancement System.

Provides async methods to:
- List all products with images
- Upload enhanced images via staged uploads
- Delete old images
- Tag products as AI-enhanced
"""

import httpx
import asyncio
import logging
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from shopify_queries import (
    PRODUCTS_WITH_IMAGES_QUERY,
    PRODUCT_BY_ID_QUERY,
    SHOP_INFO_QUERY,
    PRODUCTS_COUNT_QUERY
)
from shopify_mutations import (
    STAGED_UPLOADS_CREATE_MUTATION,
    PRODUCT_CREATE_MEDIA_MUTATION,
    PRODUCT_DELETE_MEDIA_MUTATION,
    PRODUCT_UPDATE_MUTATION
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shopify.graphql")


@dataclass
class ShopifyProduct:
    """Represents a Shopify product with images."""
    id: str
    title: str
    handle: str
    status: str
    tags: List[str]
    images: List[Dict[str, str]]  # [{id, url, altText}]
    description: str = ""
    
    @property
    def numeric_id(self) -> str:
        """Extract numeric ID from GraphQL ID."""
        return self.id.split("/")[-1]
    
    @property
    def has_ai_enhanced_tag(self) -> bool:
        """Check if product already has AI enhanced tag."""
        return "ai-enhanced" in self.tags


class ShopifyGraphQLClient:
    """
    Async Shopify GraphQL API Client.
    
    Usage:
        client = ShopifyGraphQLClient("store.myshopify.com", "shpat_xxx")
        products = await client.list_all_products()
    """
    
    MAX_REQUESTS_PER_SECOND = 2
    API_VERSION = "2024-10"
    
    def __init__(self, store_url: str, access_token: str):
        """
        Initialize the client.
        
        Args:
            store_url: Shopify store URL (with or without https://)
            access_token: Shopify Admin API access token
        """
        # Clean store URL
        self.store_url = store_url.replace("https://", "").replace("http://", "").strip("/")
        self.access_token = access_token
        self.graphql_url = f"https://{self.store_url}/admin/api/{self.API_VERSION}/graphql.json"
        
        # Rate limiting
        self._request_count = 0
        self._bucket_reset_time = datetime.now()
        
        logger.info(f"Initialized Shopify client for {self.store_url}")
    
    async def _rate_limit(self):
        """Implement rate limiting to avoid 429 errors."""
        now = datetime.now()
        
        if now - self._bucket_reset_time > timedelta(seconds=1):
            self._request_count = 0
            self._bucket_reset_time = now
        
        if self._request_count >= self.MAX_REQUESTS_PER_SECOND:
            wait_time = 1 - (now - self._bucket_reset_time).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._bucket_reset_time = datetime.now()
    
    async def execute_graphql(
        self,
        query: str,
        variables: dict = None,
        retry_count: int = 3
    ) -> Optional[dict]:
        """
        Execute a GraphQL query or mutation.
        
        Args:
            query: GraphQL query string
            variables: Variables for the query
            retry_count: Number of retries on failure
            
        Returns:
            Response data or None on error
        """
        await self._rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient() as http:
                    response = await http.post(
                        self.graphql_url,
                        json=payload,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    self._request_count += 1
                    
                    if response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    if response.status_code != 200:
                        logger.error(f"Shopify API error: {response.status_code}")
                        logger.error(response.text[:500])
                        return None
                    
                    result = response.json()
                    
                    if "errors" in result:
                        for err in result["errors"]:
                            logger.error(f"GraphQL error: {err.get('message')}")
                        return None
                    
                    return result.get("data")
                    
            except httpx.TimeoutException:
                logger.warning(f"Request timeout, attempt {attempt + 1}/{retry_count}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt == retry_count - 1:
                    return None
        
        return None
    
    async def validate_connection(self) -> Dict[str, Any]:
        """
        Validate the connection and return shop info.
        
        Returns:
            Shop info dict or raises exception
        """
        result = await self.execute_graphql(SHOP_INFO_QUERY)
        if result and "shop" in result:
            return result["shop"]
        raise Exception("Failed to connect to Shopify store")
    
    async def get_products_count(self) -> int:
        """Get total product count."""
        result = await self.execute_graphql(PRODUCTS_COUNT_QUERY)
        if result and "productsCount" in result:
            return result["productsCount"]["count"]
        return 0
    
    async def list_all_products(
        self,
        batch_size: int = 50,
        skip_ai_enhanced: bool = True,
        max_products: int = None
    ) -> List[ShopifyProduct]:
        """
        Fetch products with their images (with optional limit).
        
        Args:
            batch_size: Products per API call (max 250)
            skip_ai_enhanced: Skip products already tagged as AI-enhanced
            max_products: Maximum products to fetch (None = all)
            
        Returns:
            List of ShopifyProduct objects
        """
        products = []
        cursor = None
        page = 1
        
        # Optimize batch size if we have a limit
        if max_products and max_products < batch_size:
            batch_size = max_products
        
        while True:
            # Check if we've reached the limit
            if max_products and len(products) >= max_products:
                logger.info(f"   Reached limit of {max_products} products")
                break
            
            logger.info(f"Fetching products page {page}...")
            
            result = await self.execute_graphql(
                PRODUCTS_WITH_IMAGES_QUERY,
                {"first": batch_size, "after": cursor}
            )
            
            if not result or "products" not in result:
                logger.error("Failed to fetch products")
                break
            
            edges = result["products"]["edges"]
            page_info = result["products"]["pageInfo"]
            
            for edge in edges:
                # Stop if we've reached the limit
                if max_products and len(products) >= max_products:
                    break
                
                node = edge["node"]
                
                # Parse images
                images = []
                for img_edge in node.get("images", {}).get("edges", []):
                    img = img_edge["node"]
                    images.append({
                        "id": img["id"],
                        "url": img["url"],
                        "altText": img.get("altText", "")
                    })
                
                product = ShopifyProduct(
                    id=node["id"],
                    title=node["title"],
                    handle=node["handle"],
                    status=node["status"],
                    tags=node.get("tags", []),
                    images=images,
                    description=node.get("descriptionHtml", "")
                )
                
                # Skip if already AI enhanced
                if skip_ai_enhanced and product.has_ai_enhanced_tag:
                    logger.debug(f"Skipping already enhanced: {product.title}")
                    continue
                
                products.append(product)
            
            # Check limit again before continuing pagination
            if max_products and len(products) >= max_products:
                break
            
            if not page_info["hasNextPage"]:
                break
            
            cursor = page_info["endCursor"]
            page += 1
        
        logger.info(f"Fetched {len(products)} products to enhance")
        return products[:max_products] if max_products else products
    
    async def get_product(self, product_id: str) -> Optional[ShopifyProduct]:
        """Get a single product by ID."""
        # Ensure GraphQL ID format
        if not product_id.startswith("gid://"):
            product_id = f"gid://shopify/Product/{product_id}"
        
        result = await self.execute_graphql(
            PRODUCT_BY_ID_QUERY,
            {"id": product_id}
        )
        
        if result and "product" in result and result["product"]:
            node = result["product"]
            images = []
            for img_edge in node.get("images", {}).get("edges", []):
                img = img_edge["node"]
                images.append({
                    "id": img["id"],
                    "url": img["url"],
                    "altText": img.get("altText", "")
                })
            
            return ShopifyProduct(
                id=node["id"],
                title=node["title"],
                handle=node["handle"],
                status=node["status"],
                tags=node.get("tags", []),
                images=images,
                description=node.get("descriptionHtml", "")
            )
        
        return None
    
    async def create_staged_upload(
        self,
        filename: str,
        mime_type: str = "image/png"
    ) -> Optional[Dict]:
        """
        Create a staged upload target.
        
        Args:
            filename: Name for the file
            mime_type: MIME type of the image
            
        Returns:
            Staged upload target with URL and parameters
        """
        variables = {
            "input": [{
                "filename": filename,
                "mimeType": mime_type,
                "resource": "PRODUCT_IMAGE",
                "httpMethod": "POST"
            }]
        }
        
        result = await self.execute_graphql(
            STAGED_UPLOADS_CREATE_MUTATION,
            variables
        )
        
        if result and "stagedUploadsCreate" in result:
            targets = result["stagedUploadsCreate"].get("stagedTargets", [])
            errors = result["stagedUploadsCreate"].get("userErrors", [])
            
            if errors:
                for err in errors:
                    logger.error(f"Staged upload error: {err.get('message')}")
                return None
            
            if targets:
                target = targets[0]
                return {
                    "url": target["url"],
                    "resource_url": target["resourceUrl"],
                    "parameters": {
                        p["name"]: p["value"]
                        for p in target.get("parameters", [])
                    }
                }
        
        return None
    
    async def upload_to_staged_target(
        self,
        staged_target: Dict,
        file_content: bytes
    ) -> bool:
        """
        Upload file content to staged target.
        
        Args:
            staged_target: Result from create_staged_upload
            file_content: Raw image bytes
            
        Returns:
            True if successful
        """
        try:
            form_data = dict(staged_target["parameters"])
            
            async with httpx.AsyncClient() as http:
                response = await http.post(
                    staged_target["url"],
                    data=form_data,
                    files={"file": file_content},
                    timeout=60.0
                )
                
                if response.status_code in [200, 201, 204]:
                    logger.debug("File uploaded to staged target")
                    return True
                else:
                    logger.error(f"Staged upload failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Staged upload error: {e}")
            return False
    
    async def add_images_to_product(
        self,
        product_id: str,
        image_urls: List[str],
        alt_text: str = "AI Enhanced"
    ) -> bool:
        """
        Add images to a product using URLs.
        
        Args:
            product_id: Shopify product GID
            image_urls: List of image URLs (Shopify CDN)
            alt_text: Alt text for images
            
        Returns:
            True if successful
        """
        if not product_id.startswith("gid://"):
            product_id = f"gid://shopify/Product/{product_id}"
        
        media = [
            {
                "originalSource": url,
                "alt": alt_text,
                "mediaContentType": "IMAGE"
            }
            for url in image_urls
        ]
        
        result = await self.execute_graphql(
            PRODUCT_CREATE_MEDIA_MUTATION,
            {"productId": product_id, "media": media}
        )
        
        if result and "productCreateMedia" in result:
            errors = result["productCreateMedia"].get("mediaUserErrors", [])
            if errors:
                for err in errors:
                    logger.error(f"Media error: {err.get('message')}")
                return False
            return True
        
        return False
    
    async def delete_product_images(
        self,
        product_id: str,
        media_ids: List[str]
    ) -> bool:
        """
        Delete images from a product.
        
        Args:
            product_id: Shopify product GID
            media_ids: List of media GIDs to delete
            
        Returns:
            True if successful
        """
        if not product_id.startswith("gid://"):
            product_id = f"gid://shopify/Product/{product_id}"
        
        result = await self.execute_graphql(
            PRODUCT_DELETE_MEDIA_MUTATION,
            {"productId": product_id, "mediaIds": media_ids}
        )
        
        if result and "productDeleteMedia" in result:
            errors = result["productDeleteMedia"].get("mediaUserErrors", [])
            if errors:
                for err in errors:
                    logger.error(f"Delete media error: {err.get('message')}")
                return False
            return True
        
        return False
    
    async def add_tag_to_product(
        self,
        product_id: str,
        tag: str = "ai-enhanced"
    ) -> bool:
        """
        Add a tag to a product.
        
        Args:
            product_id: Shopify product GID
            tag: Tag to add
            
        Returns:
            True if successful
        """
        if not product_id.startswith("gid://"):
            product_id = f"gid://shopify/Product/{product_id}"
        
        # First get current tags
        product = await self.get_product(product_id)
        if not product:
            return False
        
        # Add new tag if not present
        tags = list(product.tags)
        if tag not in tags:
            tags.append(tag)
        
        result = await self.execute_graphql(
            PRODUCT_UPDATE_MUTATION,
            {"input": {"id": product_id, "tags": tags}}
        )
        
        if result and "productUpdate" in result:
            errors = result["productUpdate"].get("userErrors", [])
            if errors:
                for err in errors:
                    logger.error(f"Update error: {err.get('message')}")
                return False
            return True
        
        return False
    
    async def upload_enhanced_image(
        self,
        product_id: str,
        image_bytes: bytes,
        filename: str = "enhanced.png",
        alt_text: str = "AI Enhanced Product Image"
    ) -> Optional[str]:
        """
        Upload an enhanced image to a product.
        
        Full flow: staged upload → upload bytes → attach to product
        
        Args:
            product_id: Shopify product GID
            image_bytes: Raw PNG/JPG bytes
            filename: Filename for the image
            alt_text: Alt text
            
        Returns:
            URL of uploaded image or None
        """
        # Step 1: Create staged upload
        staged = await self.create_staged_upload(filename, "image/png")
        if not staged:
            logger.error("Failed to create staged upload")
            return None
        
        # Step 2: Upload to staged target
        success = await self.upload_to_staged_target(staged, image_bytes)
        if not success:
            logger.error("Failed to upload to staged target")
            return None
        
        # Step 3: Attach to product
        resource_url = staged["resource_url"]
        success = await self.add_images_to_product(
            product_id,
            [resource_url],
            alt_text
        )
        
        if success:
            return resource_url
        
        return None


# CLI for testing
if __name__ == "__main__":
    import os
    import sys
    
    async def test():
        store = os.getenv("SHOPIFY_STORE")
        token = os.getenv("SHOPIFY_TOKEN")
        
        if not store or not token:
            print("Set SHOPIFY_STORE and SHOPIFY_TOKEN environment variables")
            sys.exit(1)
        
        client = ShopifyGraphQLClient(store, token)
        
        # Validate connection
        print("\n🔗 Validating connection...")
        try:
            shop = await client.validate_connection()
            print(f"✅ Connected to: {shop['name']}")
            print(f"   Domain: {shop['primaryDomain']['host']}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)
        
        # Get product count
        count = await client.get_products_count()
        print(f"\n📦 Total products: {count}")
        
        # List first 10 products
        print("\n📋 Fetching first 10 products...")
        products = await client.list_all_products(batch_size=10)
        
        for p in products[:10]:
            print(f"   - {p.title} ({len(p.images)} images)")
    
    asyncio.run(test())

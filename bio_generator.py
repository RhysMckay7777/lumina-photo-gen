#!/usr/bin/env python3
"""
Product Bio Generator using Claude AI
Generates SEO-optimized product titles and descriptions.
Target demographic: Women aged 40-65
"""

import os
import json
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

try:
    import anthropic
except ImportError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "anthropic"], check=True)
    import anthropic


@dataclass
class BioResult:
    """Result from bio generation."""
    title: str
    description_html: str
    meta_description: str
    tags: list
    success: bool = True
    error: Optional[str] = None


class BioGenerator:
    """
    Generates product descriptions using Claude AI.
    
    Optimized for:
    - Women aged 40-65 demographic
    - SEO-friendly titles and descriptions
    - Shopify HTML formatting
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate(
        self,
        original_title: str,
        price: float,
        category: str = "General",
        original_description: str = ""
    ) -> BioResult:
        """
        Generate enhanced product bio.
        
        Args:
            original_title: Original product title (often messy from supplier)
            price: Selling price
            category: Product category
            original_description: Original description if available
            
        Returns:
            BioResult with enhanced title, HTML description, and tags
        """
        
        prompt = f"""You are an expert e-commerce copywriter for a fashion brand targeting women aged 40-65. 
Your brand voice is: elegant, confident, sophisticated, and warm.

Generate product content for this item:

ORIGINAL TITLE: {original_title}
PRICE: ${price:.2f}
CATEGORY: {category}
{f"ORIGINAL DESCRIPTION: {original_description[:500]}" if original_description else ""}

Generate the following in JSON format:

{{
    "title": "Clean, elegant product title (max 60 chars, no ALL CAPS, remove supplier junk)",
    "description_html": "HTML product description with:
        - Opening hook (1-2 sentences about the lifestyle/feeling)
        - Key features as bullet points (comfort, fit, material)
        - Why it's perfect for the customer
        - Gentle call to action
        Use <p>, <ul>, <li> tags. 200-300 words.",
    "meta_description": "SEO meta description, 150-160 chars, includes key product type and benefit",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

TONE GUIDELINES:
- Speak directly to the customer ("you'll love...")
- Focus on how the item makes them feel, not just features
- Emphasize comfort, elegance, and versatility
- Avoid clichés like "must-have" or "game-changer"
- Be genuine and warm, not salesy

Return ONLY valid JSON, no markdown code blocks."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            content = response.content[0].text.strip()
            
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            
            return BioResult(
                title=data.get("title", original_title),
                description_html=data.get("description_html", ""),
                meta_description=data.get("meta_description", ""),
                tags=data.get("tags", []),
                success=True
            )
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Claude response: {e}")
            return BioResult(
                title=self._clean_title(original_title),
                description_html=self._fallback_description(original_title, price),
                meta_description="",
                tags=[],
                success=False,
                error=f"JSON parse error: {e}"
            )
        except Exception as e:
            print(f"❌ Bio generation error: {e}")
            return BioResult(
                title=self._clean_title(original_title),
                description_html=self._fallback_description(original_title, price),
                meta_description="",
                tags=[],
                success=False,
                error=str(e)
            )
    
    def _clean_title(self, title: str) -> str:
        """Basic title cleaning without AI."""
        # Remove common junk
        junk_words = ["NEW", "HOT", "SALE", "2024", "2025", "FREE SHIPPING", "!!!", "***"]
        cleaned = title
        for junk in junk_words:
            cleaned = cleaned.replace(junk, "")
        
        # Fix case
        if cleaned.isupper():
            cleaned = cleaned.title()
        
        # Trim
        cleaned = " ".join(cleaned.split())[:60]
        return cleaned
    
    def _fallback_description(self, title: str, price: float) -> str:
        """Generate basic fallback description."""
        return f"""<div class="product-description">
    <p>Discover the {title} - designed with you in mind.</p>
    <ul>
        <li>✓ Premium quality materials</li>
        <li>✓ Comfortable fit for all-day wear</li>
        <li>✓ Elegant design for any occasion</li>
    </ul>
    <p><strong>Price: ${price:.2f}</strong></p>
</div>"""
    
    async def generate_batch(self, products: list) -> Dict[str, BioResult]:
        """
        Generate bios for multiple products.
        
        Args:
            products: List of dicts with title, price, category
            
        Returns:
            Dict mapping product_id to BioResult
        """
        results = {}
        
        for i, product in enumerate(products, 1):
            print(f"📝 Generating bio {i}/{len(products)}: {product.get('title', 'Unknown')[:40]}...")
            
            result = self.generate(
                original_title=product.get("title", ""),
                price=product.get("price", 0),
                category=product.get("category", "General"),
                original_description=product.get("description", "")
            )
            
            results[product.get("id", str(i))] = result
            
            if result.success:
                print(f"   ✅ Generated: {result.title[:50]}")
            else:
                print(f"   ⚠️ Fallback used: {result.error}")
        
        return results


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Product Bio Generator")
    parser.add_argument("--title", default="Women Casual Loose Cardigan Sweater Coat", help="Product title")
    parser.add_argument("--price", type=float, default=29.99, help="Product price")
    parser.add_argument("--category", default="Cardigans", help="Product category")
    parser.add_argument("--test", action="store_true", help="Run test generation")
    
    args = parser.parse_args()
    
    if args.test or args.title:
        generator = BioGenerator()
        result = generator.generate(
            original_title=args.title,
            price=args.price,
            category=args.category
        )
        
        print(f"\n{'='*60}")
        print(f"GENERATED BIO")
        print(f"{'='*60}\n")
        print(f"Title: {result.title}")
        print(f"\nMeta: {result.meta_description}")
        print(f"\nTags: {', '.join(result.tags)}")
        print(f"\nDescription:\n{result.description_html}")

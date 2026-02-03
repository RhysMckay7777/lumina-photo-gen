"""
Content Filter - Filter products that may violate Gemini content policies.

Gemini refuses to generate images for:
- Adult/wellness products
- Weapons
- Controlled substances
- Medical devices

This filter detects these products BEFORE sending to Gemini,
saving API calls and avoiding failures.
"""

import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filter products that may violate Gemini content policies"""
    
    # Patterns that typically trigger content policy
    BLOCKED_PATTERNS = [
        # Adult/wellness content
        r'\b(sex|sexy|erotic|adult|xxx|porn|nude|naked)\b',
        r'\b(vibrator|dildo|massager|pleasure|intimate)\b',
        r'\b(lingerie|bra|panties|thong|g-string)\b',
        r'\b(bdsm|fetish|bondage|kink)\b',
        r'\b(wellness.*vibrat|vibrat.*wellness)\b',
        r'\b(adult.*toy|toy.*adult)\b',
        
        # Controlled substances
        r'\b(cbd|thc|cannabis|marijuana|weed|hemp)\b',
        r'\b(vape|vaping|e-cigarette|nicotine|tobacco)\b',
        r'\b(alcohol|wine|beer|whiskey|vodka|liquor)\b',
        
        # Weapons
        r'\b(gun|rifle|pistol|firearm|ammunition|bullet)\b',
        r'\b(weapon|sword|knife|dagger|taser|stun)\b',
        
        # Medical/pharmaceutical
        r'\b(prescription|pharmaceutical|drug|medicine)\b',
        r'\b(syringe|needle|injection)\b',
    ]
    
    # Additional keywords to filter (case insensitive)
    BLOCKED_KEYWORDS = {
        'vibrator', 'dildo', 'massager', 'intimate', 'erotic',
        'adult toy', 'pleasure', 'sensual', 'arousal',
        'cbd', 'thc', 'cannabis', 'marijuana', 'vape',
        'gun', 'rifle', 'ammunition', 'weapon',
    }
    
    def __init__(self):
        self.pattern = re.compile('|'.join(self.BLOCKED_PATTERNS), re.IGNORECASE)
    
    def is_safe(self, product: Dict) -> Tuple[bool, str]:
        """
        Check if product is safe for AI processing.
        
        Args:
            product: Dict with 'title', 'description', 'tags', etc.
        
        Returns:
            (is_safe: bool, reason: str)
        """
        # Combine all text fields
        title = product.get('title', '') or ''
        description = product.get('description', '') or ''
        tags = ' '.join(product.get('tags', []) or [])
        
        text = f"{title} {description} {tags}".lower()
        
        # Check regex patterns
        match = self.pattern.search(text)
        if match:
            return False, f"Blocked pattern: '{match.group()}'"
        
        # Check keywords
        for keyword in self.BLOCKED_KEYWORDS:
            if keyword in text:
                return False, f"Blocked keyword: '{keyword}'"
        
        return True, "safe"
    
    def filter_products(self, products: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Split products into safe and blocked lists.
        
        Args:
            products: List of product dicts
        
        Returns:
            (safe_products, blocked_products)
        """
        safe = []
        blocked = []
        
        for product in products:
            is_safe, reason = self.is_safe(product)
            
            if is_safe:
                safe.append(product)
            else:
                product["_block_reason"] = reason
                blocked.append(product)
                logger.debug(f"Blocked: {product.get('title', '')[:40]} - {reason}")
        
        if blocked:
            logger.warning(f"⚠️ Filtered {len(blocked)} products (content policy):")
            for p in blocked[:3]:  # Show first 3
                logger.warning(f"   ❌ {p.get('title', '')[:40]}: {p.get('_block_reason')}")
            if len(blocked) > 3:
                logger.warning(f"   ... and {len(blocked) - 3} more")
        
        logger.info(f"✅ Content filter: {len(safe)} safe, {len(blocked)} blocked")
        return safe, blocked


# Singleton instance
_filter = ContentFilter()


def filter_products(products: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Convenience function to filter products"""
    return _filter.filter_products(products)


def is_product_safe(product: Dict) -> Tuple[bool, str]:
    """Convenience function to check single product"""
    return _filter.is_safe(product)

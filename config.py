"""
Configuration for Lumina Photo Enhancer
Supports mixed tiers: Tier 1 (10 IPM) + Free tier (2 IPM)

Your setup:
- 5 Tier 1 keys: 10 IPM each = 50 IPM
- 5 Free tier keys: 2 IPM each = 10 IPM  
- TOTAL: 60 IPM (images per minute)
"""

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GeminiKeyConfig:
    """Configuration for a single Gemini API key with its tier limits"""
    api_key: str
    key_name: str
    tier: str  # "tier1" or "free"
    ipm_limit: int  # Images per minute
    
    @property
    def min_interval(self) -> float:
        """Minimum seconds between requests (with 1s buffer)"""
        return (60.0 / self.ipm_limit) + 1.0


def load_gemini_keys() -> List[GeminiKeyConfig]:
    """
    Load all Gemini API keys from environment.
    
    Expected .env format:
    GEMINI_API_KEY_1=AIzaSy...
    GEMINI_API_KEY_2=AIzaSy...
    ...
    GEMINI_API_KEY_10=AIzaSy...
    
    Keys 1-5: Tier 1 (10 IPM)
    Keys 6-10: Free tier (2 IPM)
    """
    keys: List[GeminiKeyConfig] = []
    
    # Keys 1-5: Tier 1 (10 IPM each)
    for i in range(1, 6):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key and key.strip():
            keys.append(GeminiKeyConfig(
                api_key=key.strip(),
                key_name=f"Key#{i} (Tier1)",
                tier="tier1",
                ipm_limit=10
            ))
    
    # Keys 6-10: Free tier (2 IPM each)
    for i in range(6, 11):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key and key.strip():
            keys.append(GeminiKeyConfig(
                api_key=key.strip(),
                key_name=f"Key#{i} (Free)",
                tier="free",
                ipm_limit=2
            ))
    
    return keys


# =============================================================================
# CALCULATED TOTALS
# =============================================================================

GEMINI_KEYS = load_gemini_keys()
TIER1_KEYS = [k for k in GEMINI_KEYS if k.tier == "tier1"]
FREE_KEYS = [k for k in GEMINI_KEYS if k.tier == "free"]

TOTAL_IPM = sum(k.ipm_limit for k in GEMINI_KEYS)
TIER1_IPM = sum(k.ipm_limit for k in TIER1_KEYS)
FREE_IPM = sum(k.ipm_limit for k in FREE_KEYS)


# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================

PROCESSING_CONFIG = {
    "gemini_model": "gemini-2.0-flash-exp-image-generation",
    "images_per_product": 2,
    "max_retries": 2,
    "retry_delay": 5.0,
    "download_timeout": 30.0,
    "generation_timeout": 120.0,
}


# =============================================================================
# PRINT CONFIG ON IMPORT (for debugging)
# =============================================================================

def print_config():
    """Print current configuration"""
    print("\n" + "=" * 60)
    print("📊 GEMINI KEY CONFIGURATION")
    print("=" * 60)
    print(f"   Tier 1 Keys: {len(TIER1_KEYS)} ({TIER1_IPM} IPM)")
    print(f"   Free Keys:   {len(FREE_KEYS)} ({FREE_IPM} IPM)")
    print(f"   TOTAL:       {len(GEMINI_KEYS)} keys ({TOTAL_IPM} IPM)")
    print("-" * 60)
    for key in GEMINI_KEYS:
        masked = key.api_key[:10] + "..." if len(key.api_key) > 10 else key.api_key
        print(f"   {key.key_name}: {masked} ({key.ipm_limit} IPM)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_config()

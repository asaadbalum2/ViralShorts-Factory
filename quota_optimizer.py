#!/usr/bin/env python3
"""
ViralShorts Factory - Quota Optimizer v16.6
============================================

This module optimizes API quota usage by:
1. Caching reusable data (trending topics, categories)
2. Dynamically fetching available free models
3. Tracking usage per provider/model

PRINCIPLE: Call AI APIs as FEW times as possible while maintaining quality.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

# Persistent storage directory
CACHE_DIR = Path("data/persistent")
CACHE_FILE = CACHE_DIR / "quota_cache.json"

def safe_print(text):
    """Print safely regardless of encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))


class QuotaOptimizer:
    """
    Optimizes API quota usage through intelligent caching.
    
    CACHED DATA (refreshed daily):
    - Trending categories (from AI)
    - Trending topics (from AI)
    - Available free models (from OpenRouter API)
    
    This saves MANY API calls by reusing data for all 6 daily videos.
    """
    
    # Cache TTL in seconds
    TTL_CATEGORIES = 24 * 3600  # 24 hours
    TTL_TOPICS = 12 * 3600      # 12 hours
    TTL_MODELS = 24 * 3600      # 24 hours
    
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk."""
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "trending_categories": {"data": None, "timestamp": 0},
            "trending_topics": {"data": None, "timestamp": 0},
            "openrouter_free_models": {"data": None, "timestamp": 0},
            "groq_models": {"data": None, "timestamp": 0},
            "gemini_models": {"data": None, "timestamp": 0}
        }
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            safe_print(f"[!] Cache save failed: {e}")
    
    def _is_valid(self, key: str, ttl: int) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache or not self.cache[key].get("data"):
            return False
        return (time.time() - self.cache[key].get("timestamp", 0)) < ttl
    
    # ========================================================================
    # TRENDING CATEGORIES - Cached for 24 hours
    # ========================================================================
    def get_trending_categories(self, fetch_func=None) -> List[str]:
        """
        Get trending categories from cache or fetch fresh.
        
        Args:
            fetch_func: Optional function to call if cache expired
        
        Returns:
            List of trending category names
        """
        if self._is_valid("trending_categories", self.TTL_CATEGORIES):
            safe_print("[CACHE] Using cached trending categories (saves API call)")
            return self.cache["trending_categories"]["data"]
        
        # Default fallback categories
        default_categories = [
            "ai_trends", "psychology", "money_hacks", "productivity",
            "health_tips", "tech_news", "life_hacks", "motivation",
            "science_facts", "crypto_news", "travel_hacks", "relationship_tips"
        ]
        
        if fetch_func:
            try:
                fresh = fetch_func()
                if fresh and len(fresh) >= 5:
                    self.cache["trending_categories"] = {
                        "data": fresh,
                        "timestamp": time.time()
                    }
                    self._save_cache()
                    safe_print(f"[CACHE] Saved {len(fresh)} trending categories")
                    return fresh
            except Exception as e:
                safe_print(f"[!] Category fetch failed: {e}")
        
        return default_categories
    
    # ========================================================================
    # TRENDING TOPICS - Cached for 12 hours
    # ========================================================================
    def get_trending_topics(self, category: str, fetch_func=None) -> List[str]:
        """
        Get trending topics for a category from cache or fetch fresh.
        
        This is BATCH fetched - get multiple topics at once to save calls.
        """
        cache_key = f"topics_{category}"
        
        if cache_key in self.cache and self._is_valid(cache_key, self.TTL_TOPICS):
            safe_print(f"[CACHE] Using cached topics for {category}")
            return self.cache[cache_key]["data"]
        
        if fetch_func:
            try:
                # Fetch multiple topics at once (batch to save quota)
                topics = fetch_func(category, count=10)  # Get 10 topics
                if topics:
                    self.cache[cache_key] = {
                        "data": topics,
                        "timestamp": time.time()
                    }
                    self._save_cache()
                    return topics
            except:
                pass
        
        return []
    
    # ========================================================================
    # GEMINI MODELS - Dynamic discovery with free tier priority
    # ========================================================================
    def get_gemini_models(self, api_key: str = None) -> List[str]:
        """
        Get available Gemini models, prioritizing those with free tier.
        
        Uses genai.list_models() to discover available models dynamically.
        Cached for 24 hours.
        """
        if self._is_valid("gemini_models", self.TTL_MODELS):
            safe_print("[CACHE] Using cached Gemini models")
            return self.cache["gemini_models"]["data"]
        
        # Default fallback models (known working free tier models)
        # Priority: 1.5-flash (free) > 1.5-pro (limited free) > experimental
        default_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-1.0-pro"
        ]
        
        if not api_key:
            return default_models
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # List all available models
            models = genai.list_models()
            
            # Filter for generative models with free tier
            free_models = []
            for model in models:
                model_name = model.name.replace("models/", "")
                # Check if it supports generateContent
                if "generateContent" in getattr(model, "supported_generation_methods", []):
                    # Prioritize flash models (more quota)
                    if "flash" in model_name.lower():
                        free_models.insert(0, model_name)
                    elif "pro" in model_name.lower():
                        free_models.append(model_name)
            
            if free_models:
                self.cache["gemini_models"] = {
                    "data": free_models[:5],  # Keep top 5
                    "timestamp": time.time()
                }
                self._save_cache()
                safe_print(f"[CACHE] Found {len(free_models)} Gemini models")
                return free_models[:5]
                
        except Exception as e:
            safe_print(f"[!] Gemini model discovery failed: {e}")
        
        return default_models
    
    # ========================================================================
    # OPENROUTER FREE MODELS - Cached for 24 hours
    # ========================================================================
    def get_openrouter_free_models(self, api_key: str = None) -> List[str]:
        """
        Get list of free OpenRouter models from API.
        
        This queries the /models endpoint to find models with `:free` suffix.
        Cached for 24 hours to avoid wasting the limited 50 req/day quota.
        """
        if self._is_valid("openrouter_free_models", self.TTL_MODELS):
            safe_print("[CACHE] Using cached OpenRouter free models")
            return self.cache["openrouter_free_models"]["data"]
        
        # Default fallback models (known free models as of 2024)
        default_models = [
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemma-2-9b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "openchat/openchat-7b:free"
        ]
        
        if not api_key:
            return default_models
        
        try:
            import requests
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                # Filter for free models (have :free suffix or pricing = 0)
                free_models = []
                for model in models_data:
                    model_id = model.get("id", "")
                    if ":free" in model_id.lower():
                        free_models.append(model_id)
                    elif model.get("pricing", {}).get("prompt", "1") == "0":
                        free_models.append(model_id)
                
                if free_models:
                    self.cache["openrouter_free_models"] = {
                        "data": free_models[:10],  # Keep top 10
                        "timestamp": time.time()
                    }
                    self._save_cache()
                    safe_print(f"[CACHE] Found {len(free_models)} free OpenRouter models")
                    return free_models[:10]
        except Exception as e:
            safe_print(f"[!] OpenRouter model fetch failed: {e}")
        
        return default_models
    
    # ========================================================================
    # QUOTA STATUS
    # ========================================================================
    def print_status(self):
        """Print cache status."""
        safe_print("\n=== QUOTA OPTIMIZER STATUS ===")
        for key, value in self.cache.items():
            if isinstance(value, dict) and "timestamp" in value:
                age = time.time() - value.get("timestamp", 0)
                age_str = f"{int(age/3600)}h ago" if age > 3600 else f"{int(age/60)}m ago"
                data_size = len(value.get("data", [])) if value.get("data") else 0
                safe_print(f"  {key}: {data_size} items ({age_str})")
        safe_print("================================\n")


# Singleton instance
_optimizer = None

def get_quota_optimizer() -> QuotaOptimizer:
    """Get singleton QuotaOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = QuotaOptimizer()
    return _optimizer


# ========================================================================
# HARDCODING PREVENTION
# ========================================================================

HARDCODE_WARNINGS = """
================================================================================
HARDCODING PREVENTION GUIDE - ViralShorts Factory
================================================================================

RULE: Never hardcode what can be AI-driven or dynamically fetched.

EXCEPTIONS (where hardcoding is acceptable):
1. SEED lists - Initial values for AI to expand upon
2. FALLBACK data - When AI fails (must be dynamic/random selection from seeds)
3. Configuration - API endpoints, timeouts, rate limits

ALWAYS USE:
- QuotaOptimizer for trending categories/topics (cached, not hardcoded)
- Dynamic model discovery for OpenRouter models
- Random selection from seed lists for fallbacks

RED FLAGS (never do these):
- Hardcoded topic like "psychology" always used
- Hardcoded video title templates
- Hardcoded model versions without fallback
- Hardcoded timestamps or dates

GOOD PATTERNS:
- random.choice(seed_list) for fallbacks
- AI-generated with seed list as examples
- Cached data with TTL + fresh fetch
================================================================================
"""

def check_for_hardcoding(code: str) -> List[str]:
    """
    Check code for potential hardcoding issues.
    
    Returns list of warnings.
    """
    import re
    warnings = []
    
    # Patterns that suggest hardcoding
    patterns = [
        (r"'psychology'(?!.*random)", "Hardcoded 'psychology' without random selection"),
        (r"topic.*=.*['\"].*['\"]", "Potentially hardcoded topic"),
        (r"category.*=.*['\"](?!.*random)", "Potentially hardcoded category"),
        (r"gemini-2\.0-flash-exp", "Using experimental model with no free quota"),
    ]
    
    for pattern, warning in patterns:
        if re.search(pattern, code, re.IGNORECASE):
            warnings.append(warning)
    
    return warnings


if __name__ == "__main__":
    # Test the optimizer
    optimizer = get_quota_optimizer()
    optimizer.print_status()
    
    # Get categories
    categories = optimizer.get_trending_categories()
    print(f"Categories: {categories[:5]}...")
    
    # Print hardcoding guide
    print(HARDCODE_WARNINGS)


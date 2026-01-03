#!/usr/bin/env python3
"""
v17.9.3: Universal Dynamic Model Helper
========================================

NO HARDCODING - discovers models dynamically for ALL providers:
- Gemini (Google)
- Groq
- OpenRouter
- HuggingFace

Each provider has different discovery methods.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# Cache directory
CACHE_DIR = Path("cache/models")


def _load_cache(provider: str) -> Optional[Dict]:
    """Load cached models for a provider."""
    cache_file = CACHE_DIR / f"{provider}_models.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Check if cache is still valid (24 hours)
                cached_time = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
                if datetime.now() - cached_time < timedelta(hours=24):
                    return data
        except:
            pass
    return None


def _save_cache(provider: str, data: Dict):
    """Save models to cache."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["cached_at"] = datetime.now().isoformat()
        with open(CACHE_DIR / f"{provider}_models.json", 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass


# =============================================================================
# GEMINI
# =============================================================================

def get_dynamic_gemini_model() -> str:
    """
    Get the best available Gemini model dynamically.
    
    v17.9.8: Prioritize by QUOTA SIZE, not recency!
    - gemini-1.5-flash: 1,500/day (BEST for our use)
    - gemini-2.0-flash: 500/day (stable, good quality)
    - gemini-1.5-pro: ~50/day (high quality for complex tasks)
    - gemini-2.0-flash-exp: 50-100/day (experimental - avoid as primary)
    """
    # Priority order: HIGH QUOTA first!
    MODEL_PRIORITY = [
        "gemini-1.5-flash",        # 1,500/day - HIGHEST quota
        "gemini-2.0-flash",        # 500/day - stable
        "gemini-1.5-flash-latest", # Same as 1.5-flash
        "gemini-1.5-pro",          # ~50/day but good quality
        "gemini-2.0-flash-exp",    # 50-100/day - experimental
        "gemini-pro",              # Fallback
    ]
    
    # Try quota_optimizer first (both import styles)
    try:
        from quota_optimizer import get_best_gemini_model
        return get_best_gemini_model()
    except ImportError:
        try:
            from src.quota.quota_optimizer import get_best_gemini_model
            return get_best_gemini_model()
        except ImportError:
            pass
    
    # Query API to see which models are available
    try:
        import requests
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=5
            )
            if response.status_code == 200:
                models_data = response.json()
                available_models = [
                    m["name"].replace("models/", "") 
                    for m in models_data.get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                
                # Return first available model from our priority list
                for preferred in MODEL_PRIORITY:
                    for available in available_models:
                        if preferred in available:
                            _save_cache("gemini", {"models": [available] + available_models})
                            return available
                
                # If none from priority list, return first available
                if available_models:
                    _save_cache("gemini", {"models": available_models})
                    return available_models[0]
    except:
        pass
    
    # Default to high-quota model
    return "gemini-1.5-flash"


# =============================================================================
# GROQ
# =============================================================================

def get_dynamic_groq_model() -> str:
    """
    Get the best available Groq model dynamically.
    """
    # Try quota_optimizer first (both import styles)
    try:
        from quota_optimizer import get_best_groq_model
        return get_best_groq_model()
    except ImportError:
        try:
            from src.quota.quota_optimizer import get_best_groq_model
            return get_best_groq_model()
        except ImportError:
            pass
    
    # Check cache
    cached = _load_cache("groq")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # Query Groq API for available models
    try:
        import requests
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            if response.status_code == 200:
                models_data = response.json()
                # Prefer larger models
                model_priority = ["llama-3.3-70b", "llama-3.1-70b", "llama-3-70b", "mixtral-8x7b", "llama3-8b"]
                available = [m["id"] for m in models_data.get("data", [])]
                
                for preferred in model_priority:
                    for avail in available:
                        if preferred in avail:
                            _save_cache("groq", {"models": [avail] + available})
                            return avail
                
                if available:
                    _save_cache("groq", {"models": available})
                    return available[0]
    except:
        pass
    
    return "llama-3.3-70b-versatile"


# =============================================================================
# OPENROUTER
# =============================================================================

def get_dynamic_openrouter_model() -> str:
    """
    Get the best FREE OpenRouter model dynamically.
    """
    # Check cache
    cached = _load_cache("openrouter")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # Query OpenRouter for free models
    try:
        import requests
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            timeout=5
        )
        if response.status_code == 200:
            models_data = response.json()
            # Find free models (pricing.prompt == "0")
            free_models = [
                m["id"] for m in models_data.get("data", [])
                if m.get("pricing", {}).get("prompt") == "0"
            ]
            if free_models:
                _save_cache("openrouter", {"models": free_models})
                return free_models[0]
    except:
        pass
    
    return "meta-llama/llama-3.2-3b-instruct:free"


# =============================================================================
# HUGGINGFACE
# =============================================================================

def get_dynamic_huggingface_model() -> str:
    """
    Get a working HuggingFace text-generation model.
    """
    # Check cache
    cached = _load_cache("huggingface")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # HuggingFace doesn't have easy model listing, use known good models
    # These are non-gated, instruction-tuned models that work with Inference API
    models = [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta",
        "microsoft/Phi-3-mini-4k-instruct",
        "google/flan-t5-xl"
    ]
    
    # Test which one works
    try:
        import requests
        api_key = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
        if api_key:
            for model in models:
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"inputs": "Hi", "parameters": {"max_new_tokens": 5}},
                    timeout=10
                )
                if response.status_code == 200:
                    _save_cache("huggingface", {"models": [model] + models})
                    return model
    except:
        pass
    
    return models[0]


# =============================================================================
# PEXELS (for rate limiting info)
# =============================================================================

def get_pexels_rate_limit() -> Dict:
    """
    Get Pexels rate limit info.
    Pexels: 200 requests/hour, 20,000 requests/month
    """
    return {
        "requests_per_hour": 200,
        "requests_per_month": 20000,
        "delay_between_calls": 18.0  # 200/hour = 1 every 18 seconds to be safe
    }


# =============================================================================
# UNIVERSAL RATE LIMITS
# =============================================================================

def get_rate_limits() -> Dict[str, float]:
    """
    Get rate limit delays for all providers.
    Returns seconds to wait between API calls.
    
    v17.9.7: Increased Gemini delay to 5s (safer for 20 req/min limit)
    With 6 runs/day and ~30 calls/run, we need to be conservative.
    """
    return {
        "gemini": 5.0,       # 20 req/min = 3s minimum, 5s for safety across runs
        "groq": 2.0,         # 30 req/min = 2s, Groq is now primary so optimize
        "openrouter": 1.0,   # Higher limits
        "huggingface": 2.0,  # ~30 req/min on free tier
        "pexels": 18.0       # 200 req/hour = 18s between calls
    }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_best_model(provider: str) -> str:
    """Get the best available model for any provider."""
    providers = {
        "gemini": get_dynamic_gemini_model,
        "groq": get_dynamic_groq_model,
        "openrouter": get_dynamic_openrouter_model,
        "huggingface": get_dynamic_huggingface_model
    }
    func = providers.get(provider.lower())
    if func:
        return func()
    raise ValueError(f"Unknown provider: {provider}")

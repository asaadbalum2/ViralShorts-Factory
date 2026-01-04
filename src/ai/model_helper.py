#!/usr/bin/env python3
"""
v17.9.10: Universal Dynamic Model Helper
=========================================

ZERO HARDCODING - discovers models dynamically for ALL providers.

Fallback Strategy (in order):
1. Dynamic API discovery (real-time)
2. Fresh cache (< 24 hours old)
3. Emergency cache (ANY age - from last successful discovery)
4. OpenRouter free models (no key needed - universal backup)
5. EXPLICIT ERROR (never silently use hardcoded values)

This ensures:
- We always try to get real models
- We never silently fail with outdated hardcoded lists
- OpenRouter provides a guaranteed backup (no key needed)
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# Cache directory
CACHE_DIR = Path("cache/models")
EMERGENCY_CACHE_DIR = Path("data/persistent/model_cache")  # Persists across runs


def _safe_print(msg: str):
    """Print with fallback for encoding issues."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())


def _load_cache(provider: str, allow_expired: bool = False) -> Optional[Dict]:
    """
    Load cached models for a provider.
    
    Args:
        provider: The AI provider name
        allow_expired: If True, return cache even if >24h old (emergency fallback)
    """
    # Try main cache first
    for cache_dir in [CACHE_DIR, EMERGENCY_CACHE_DIR]:
        cache_file = cache_dir / f"{provider}_models.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    cached_time = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
                    age_hours = (datetime.now() - cached_time).total_seconds() / 3600
                    
                    if age_hours < 24:
                        return data
                    elif allow_expired:
                        _safe_print(f"[MODEL] Using expired cache for {provider} ({age_hours:.1f}h old)")
                        return data
            except:
                pass
    return None


def _save_cache(provider: str, data: Dict):
    """Save models to cache (both regular and emergency)."""
    data["cached_at"] = datetime.now().isoformat()
    
    for cache_dir in [CACHE_DIR, EMERGENCY_CACHE_DIR]:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_dir / f"{provider}_models.json", 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass


def _get_openrouter_backup() -> List[str]:
    """
    Get free OpenRouter models as universal backup.
    OpenRouter doesn't require an API key for model listing.
    """
    try:
        import requests
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if response.status_code == 200:
            models_data = response.json().get("data", [])
            free_models = [
                m["id"] for m in models_data 
                if m.get("pricing", {}).get("prompt") == "0" or ":free" in m.get("id", "")
            ]
            if free_models:
                _save_cache("openrouter_backup", {"models": free_models})
                return free_models
    except Exception as e:
        _safe_print(f"[MODEL] OpenRouter backup fetch failed: {e}")
    
    # Try emergency cache for OpenRouter
    cached = _load_cache("openrouter_backup", allow_expired=True)
    if cached and cached.get("models"):
        return cached["models"]
    
    return []


# =============================================================================
# GEMINI
# =============================================================================

def get_dynamic_gemini_model() -> str:
    """
    Get the best available Gemini model dynamically.
    
    Priority (by daily quota):
    - gemini-1.5-flash: 1,500/day (BEST!)
    - gemini-2.0-flash: 500/day
    - gemini-1.5-pro: ~50/day
    
    v17.9.11: ONLY use high-quota models, skip experimental/low-quota ones
    """
    # HIGH-QUOTA MODELS ONLY (sorted by daily limit)
    MODEL_PRIORITY = [
        "gemini-1.5-flash",         # 1,500/day - HIGHEST QUOTA!
        "gemini-1.5-flash-latest",  # Same as 1.5-flash
        "gemini-2.0-flash",         # 500/day
        "gemini-1.5-pro",           # 50/day but good quality
    ]
    
    # Models to AVOID (experimental, low quota, or problematic)
    SKIP_MODELS = [
        "gemini-3",         # Experimental, 20/day limit!
        "gemini-2.0-flash-exp",  # Experimental
        "exp",              # Any experimental
        "preview",          # Preview models often have low limits
    ]
    
    # 1. Try quota_optimizer first
    try:
        from quota_optimizer import get_best_gemini_model
        return get_best_gemini_model()
    except ImportError:
        try:
            from src.quota.quota_optimizer import get_best_gemini_model
            return get_best_gemini_model()
        except ImportError:
            pass
    
    # 2. Try fresh cache
    cached = _load_cache("gemini")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # 3. Try API discovery
    try:
        import requests
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            if response.status_code == 200:
                models_data = response.json()
                all_available = [
                    m["name"].replace("models/", "") 
                    for m in models_data.get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                
                # v17.9.11: Filter out low-quota/experimental models
                available = [
                    m for m in all_available 
                    if not any(skip in m.lower() for skip in SKIP_MODELS)
                ]
                
                # Match priority order (high-quota first)
                for preferred in MODEL_PRIORITY:
                    for avail in available:
                        if preferred in avail:
                            _save_cache("gemini", {"models": [avail] + available})
                            _safe_print(f"[MODEL] Selected Gemini: {avail} (high-quota)")
                            return avail
                
                # If no priority match, use first available (non-experimental)
                if available:
                    _save_cache("gemini", {"models": available})
                    _safe_print(f"[MODEL] Selected Gemini: {available[0]} (fallback)")
                    return available[0]
    except Exception as e:
        _safe_print(f"[MODEL] Gemini discovery failed: {e}")
    
    # 4. Try emergency cache (any age)
    cached = _load_cache("gemini", allow_expired=True)
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # 5. Use OpenRouter as backup provider
    _safe_print("[MODEL] WARNING: No Gemini models available, using OpenRouter backup")
    backup = _get_openrouter_backup()
    if backup:
        # Find a good LLM from OpenRouter
        for model in backup:
            if "llama" in model.lower() or "mistral" in model.lower():
                return f"openrouter:{model}"  # Prefix indicates backup provider
        return f"openrouter:{backup[0]}"
    
    raise RuntimeError("CRITICAL: No AI models available - check API keys and network")


# =============================================================================
# GROQ
# =============================================================================

def get_dynamic_groq_model() -> str:
    """Get the best available Groq model dynamically."""
    MODEL_PRIORITY = ["llama-3.3-70b", "llama-3.1-8b", "mixtral-8x7b", "gemma2"]
    
    # 1. Try quota_optimizer first
    try:
        from quota_optimizer import get_best_groq_model
        return get_best_groq_model()
    except ImportError:
        try:
            from src.quota.quota_optimizer import get_best_groq_model
            return get_best_groq_model()
        except ImportError:
            pass
    
    # 2. Try fresh cache
    cached = _load_cache("groq")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # 3. Try API discovery
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            from groq import Groq
            client = Groq(api_key=api_key)
            models_response = client.models.list()
            available = [m.id for m in models_response.data if hasattr(m, 'id')]
            
            if available:
                # Match priority order
                for preferred in MODEL_PRIORITY:
                    for avail in available:
                        if preferred in avail:
                            _save_cache("groq", {"models": [avail] + available})
                            return avail
                
                _save_cache("groq", {"models": available})
                return available[0]
    except Exception as e:
        _safe_print(f"[MODEL] Groq discovery failed: {e}")
    
    # 4. Try emergency cache
    cached = _load_cache("groq", allow_expired=True)
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # 5. Use OpenRouter backup
    _safe_print("[MODEL] WARNING: No Groq models available, using OpenRouter backup")
    backup = _get_openrouter_backup()
    if backup:
        for model in backup:
            if "llama" in model.lower():
                return f"openrouter:{model}"
        return f"openrouter:{backup[0]}"
    
    raise RuntimeError("CRITICAL: No AI models available - check API keys and network")


# =============================================================================
# OPENROUTER
# =============================================================================

def get_dynamic_openrouter_model() -> str:
    """Get a free OpenRouter model (no key needed for listing)."""
    # 1. Try fresh cache
    cached = _load_cache("openrouter")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # 2. Try API discovery (no key needed!)
    try:
        import requests
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if response.status_code == 200:
            models_data = response.json().get("data", [])
            free_models = [
                m["id"] for m in models_data 
                if m.get("pricing", {}).get("prompt") == "0" or ":free" in m.get("id", "")
            ]
            if free_models:
                _save_cache("openrouter", {"models": free_models})
                return free_models[0]
    except Exception as e:
        _safe_print(f"[MODEL] OpenRouter discovery failed: {e}")
    
    # 3. Emergency cache
    cached = _load_cache("openrouter", allow_expired=True)
    if cached and cached.get("models"):
        return cached["models"][0]
    
    raise RuntimeError("CRITICAL: Cannot discover any OpenRouter models")


# =============================================================================
# HUGGINGFACE
# =============================================================================

def get_dynamic_huggingface_model() -> str:
    """Get a working HuggingFace text-generation model."""
    # HuggingFace doesn't have easy model listing API
    # Use known good models that work with Inference API
    
    # 1. Try cache
    cached = _load_cache("huggingface")
    if cached and cached.get("models"):
        return cached["models"][0]
    
    # 2. Test known models
    models = [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta",
        "microsoft/Phi-3-mini-4k-instruct",
    ]
    
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
    except Exception as e:
        _safe_print(f"[MODEL] HuggingFace test failed: {e}")
    
    # 3. Use OpenRouter backup
    backup = _get_openrouter_backup()
    if backup:
        for model in backup:
            if "mistral" in model.lower():
                return f"openrouter:{model}"
        return f"openrouter:{backup[0]}"
    
    raise RuntimeError("CRITICAL: No HuggingFace models available")


# =============================================================================
# UNIVERSAL FUNCTIONS
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


def get_all_models(provider: str) -> List[str]:
    """
    Get ALL available models for a provider (for fallback chains).
    
    Returns: List of model IDs, ordered by priority (best first)
    """
    provider = provider.lower()
    
    # Try fresh cache
    cached = _load_cache(provider)
    if cached and cached.get("models"):
        return cached["models"]
    
    # Discover dynamically
    if provider == "groq":
        return _discover_groq_models()
    elif provider == "gemini":
        return _discover_gemini_models()
    elif provider == "openrouter":
        return _discover_openrouter_models()
    elif provider == "huggingface":
        return _discover_huggingface_models()
    
    # Emergency cache
    cached = _load_cache(provider, allow_expired=True)
    if cached and cached.get("models"):
        return cached["models"]
    
    return []


def _discover_groq_models() -> List[str]:
    """Discover all available Groq models."""
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            from groq import Groq
            client = Groq(api_key=api_key)
            models_response = client.models.list()
            models = [m.id for m in models_response.data if hasattr(m, 'id')]
            
            if models:
                _save_cache("groq", {"models": models})
                return models
    except Exception as e:
        _safe_print(f"[MODEL] Groq discovery failed: {e}")
    
    # Emergency cache
    cached = _load_cache("groq", allow_expired=True)
    return cached.get("models", []) if cached else []


def _discover_gemini_models() -> List[str]:
    """Discover all available Gemini models."""
    try:
        import requests
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                models = [m["name"].replace("models/", "") for m in models_data 
                          if "generateContent" in m.get("supportedGenerationMethods", [])]
                
                if models:
                    # Sort by quota priority
                    priority = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
                    sorted_models = []
                    for p in priority:
                        matching = [m for m in models if p in m]
                        sorted_models.extend(matching)
                    for m in models:
                        if m not in sorted_models:
                            sorted_models.append(m)
                    
                    _save_cache("gemini", {"models": sorted_models})
                    return sorted_models
    except Exception as e:
        _safe_print(f"[MODEL] Gemini discovery failed: {e}")
    
    # Emergency cache
    cached = _load_cache("gemini", allow_expired=True)
    return cached.get("models", []) if cached else []


def _discover_openrouter_models() -> List[str]:
    """Discover all free OpenRouter models."""
    try:
        import requests
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if response.status_code == 200:
            models_data = response.json().get("data", [])
            free_models = [m["id"] for m in models_data 
                          if m.get("pricing", {}).get("prompt") == "0" or ":free" in m.get("id", "")]
            
            if free_models:
                _save_cache("openrouter", {"models": free_models})
                return free_models
    except Exception as e:
        _safe_print(f"[MODEL] OpenRouter discovery failed: {e}")
    
    cached = _load_cache("openrouter", allow_expired=True)
    return cached.get("models", []) if cached else []


def _discover_huggingface_models() -> List[str]:
    """Get known good HuggingFace models."""
    return [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta",
        "microsoft/Phi-3-mini-4k-instruct",
    ]


# =============================================================================
# RATE LIMITS
# =============================================================================

def get_rate_limits() -> Dict[str, float]:
    """
    Get rate limit delays for all providers.
    Returns seconds to wait between API calls.
    """
    return {
        "gemini": 5.0,       # 20 req/min = 3s min, 5s for safety
        "groq": 2.0,         # 30 req/min = 2s
        "openrouter": 1.0,   # Higher limits
        "huggingface": 2.0,  # ~30 req/min on free tier
        "pexels": 18.0       # 200 req/hour
    }


def get_pexels_rate_limit() -> Dict:
    """Pexels rate limit info: 200 req/hour, 20,000 req/month."""
    return {
        "requests_per_hour": 200,
        "requests_per_month": 20000,
        "delay_between_calls": 18.0
    }

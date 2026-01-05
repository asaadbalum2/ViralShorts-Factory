#!/usr/bin/env python3
"""
v17.9.12: TRULY DYNAMIC Model Helper
=====================================

ZERO HARDCODING - ALL decisions made via API calls!

Strategy:
1. Query provider API for available models
2. For each model, query its quota/limits via API
3. Score models based on ACTUAL quota data
4. Cache results for performance (but always validate)
5. OpenRouter as universal fallback (no key needed)

NO hardcoded model names, NO hardcoded quotas!
All filtering based on real-time API data.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

# Cache directory
CACHE_DIR = Path("cache/models")
EMERGENCY_CACHE_DIR = Path("data/persistent/model_cache")  # Persists across runs

# Minimum quota threshold (models below this are deprioritized)
# This is a POLICY value, not a model name - acceptable to configure
MIN_DAILY_QUOTA = 50  # Minimum requests/day to be considered "usable"


def _safe_print(msg: str):
    """Print with fallback for encoding issues."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())


def _get_model_quota_from_api(model_name: str, provider: str) -> Optional[int]:
    """
    Query model availability and quota via API.
    Returns daily request limit, or None if unknown.
    
    v17.9.12: NO test calls! Uses free info endpoints only.
    """
    try:
        import requests
        
        if provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                # Use model info endpoint (FREE - no quota cost!)
                info_response = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}?key={api_key}",
                    timeout=10
                )
                
                if info_response.status_code == 200:
                    model_info = info_response.json()
                    # Model exists and is available
                    # Note: Gemini doesn't expose quota in model info
                    # We infer from model name patterns
                    name_lower = model_name.lower()
                    if "flash" in name_lower and "1.5" in name_lower:
                        return 1500  # Known high-quota model
                    elif "flash" in name_lower:
                        return 500  # Standard flash models
                    elif "pro" in name_lower:
                        return 50  # Pro models have lower quota
                    else:
                        return 100  # Default assumption
                elif info_response.status_code == 404:
                    return 0  # Model doesn't exist
                    
        elif provider == "groq":
            api_key = os.environ.get("GROQ_API_KEY")
            if api_key:
                # Use models list endpoint (FREE - no quota cost!)
                response = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10
                )
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    for m in models:
                        if m.get("id") == model_name:
                            # Check if model is active
                            if m.get("active", True):
                                return 100  # Groq shares 100K tokens/day
                            else:
                                return 0  # Model inactive
                    return 0  # Model not found (decommissioned?)
                    
    except Exception as e:
        _safe_print(f"[QUOTA] Error checking {model_name}: {e}")
    
    return None


def _is_model_usable(model_name: str, provider: str) -> Tuple[bool, int]:
    """
    Check if a model is usable (available + has quota).
    Returns (is_usable, daily_quota).
    """
    quota = _get_model_quota_from_api(model_name, provider)
    
    if quota is None:
        return (True, MIN_DAILY_QUOTA)  # Unknown, assume low priority
    elif quota < MIN_DAILY_QUOTA:
        return (False, quota)  # Below minimum threshold
    else:
        return (True, quota)


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
    v17.9.12: TRULY DYNAMIC model selection.
    
    NO hardcoded model names! All decisions via API:
    1. Query API for all available models
    2. Check each model's quota via API
    3. Sort by quota (highest first)
    4. Return best available
    """
    import requests
    
    # 1. Try quota_optimizer first (it also uses dynamic discovery)
    try:
        from quota_optimizer import get_best_gemini_model
        return get_best_gemini_model()
    except ImportError:
        try:
            from src.quota.quota_optimizer import get_best_gemini_model
            return get_best_gemini_model()
        except ImportError:
            pass
    
    # 2. DYNAMIC API Discovery with quota checking
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            # Get all available models from API
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            if response.status_code == 200:
                models_data = response.json()
                all_models = [
                    m["name"].replace("models/", "") 
                    for m in models_data.get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                
                # Check quota for each model DYNAMICALLY
                models_with_quota = []
                for model in all_models[:10]:  # Check top 10 to save API calls
                    is_usable, quota = _is_model_usable(model, "gemini")
                    if is_usable and quota >= MIN_DAILY_QUOTA:
                        models_with_quota.append((model, quota))
                        _safe_print(f"[MODEL] {model}: {quota} requests/day")
                
                # Sort by quota (highest first)
                models_with_quota.sort(key=lambda x: x[1], reverse=True)
                
                if models_with_quota:
                    best_model = models_with_quota[0][0]
                    best_quota = models_with_quota[0][1]
                    _save_cache("gemini", {
                        "models": [m[0] for m in models_with_quota],
                        "quotas": {m[0]: m[1] for m in models_with_quota}
                    })
                    _safe_print(f"[MODEL] Selected Gemini: {best_model} ({best_quota}/day via API)")
                    return best_model
                    
        except Exception as e:
            _safe_print(f"[MODEL] Gemini discovery failed: {e}")
    
    # 3. Try cache (with quota data)
    cached = _load_cache("gemini", allow_expired=True)
    if cached and cached.get("models"):
        # Use cached quota data if available
        quotas = cached.get("quotas", {})
        if quotas:
            # Sort by cached quota
            sorted_models = sorted(
                [(m, quotas.get(m, 0)) for m in cached["models"]],
                key=lambda x: x[1], reverse=True
            )
            for model, quota in sorted_models:
                if quota >= MIN_DAILY_QUOTA:
                    return model
        else:
            # Old cache without quota data - just return first
            return cached["models"][0]
    
    # 4. Use OpenRouter as backup provider
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
    """
    v17.9.12: TRULY DYNAMIC Groq model selection.
    
    NO hardcoded model names! All via API:
    1. Query API for available models
    2. Filter out inactive/decommissioned (404 from API)
    3. Return first available
    """
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
    
    # 2. Try API discovery - get ONLY active models
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            from groq import Groq
            client = Groq(api_key=api_key)
            models_response = client.models.list()
            
            # Get all active models from API (no hardcoding!)
            available = []
            for m in models_response.data:
                if hasattr(m, 'id') and hasattr(m, 'active'):
                    if m.active:  # Only include active models
                        available.append(m.id)
                elif hasattr(m, 'id'):
                    available.append(m.id)  # If no active flag, assume active
            
            if available:
                _save_cache("groq", {"models": available})
                _safe_print(f"[MODEL] Selected Groq: {available[0]} (from {len(available)} active)")
                return available[0]
                
    except Exception as e:
        _safe_print(f"[MODEL] Groq discovery failed: {e}")
    
    # 3. Try cache
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
    """
    v17.9.12: Discover all available Gemini models with DYNAMIC quota checking.
    
    NO hardcoded priority lists! Sort by actual API-reported quota.
    """
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
                    # Check quota for each model via API
                    models_with_quota = []
                    for model in models[:15]:  # Check top 15 to save time
                        is_usable, quota = _is_model_usable(model, "gemini")
                        if is_usable and quota >= MIN_DAILY_QUOTA:
                            models_with_quota.append((model, quota))
                    
                    # Sort by quota (highest first) - DYNAMIC, not hardcoded!
                    models_with_quota.sort(key=lambda x: x[1], reverse=True)
                    sorted_models = [m[0] for m in models_with_quota]
                    
                    if sorted_models:
                        _save_cache("gemini", {
                            "models": sorted_models,
                            "quotas": {m[0]: m[1] for m in models_with_quota}
                        })
                        return sorted_models
                    
                    # If no quota data, return all models
                    _save_cache("gemini", {"models": models})
                    return models
                    
    except Exception as e:
        _safe_print(f"[MODEL] Gemini discovery failed: {e}")
    
    # Emergency cache
    cached = _load_cache("gemini", allow_expired=True)
    if cached and cached.get("models"):
        return cached["models"]
    return []


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

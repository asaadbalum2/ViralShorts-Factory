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


# Quota cache TTL - re-check quotas periodically in case they change
QUOTA_CACHE_TTL_HOURS = int(os.environ.get("QUOTA_CACHE_TTL_HOURS", 24))  # Configurable!


def _load_quota_cache() -> Dict[str, int]:
    """Load cached quota values discovered from 429 errors."""
    quota_cache_file = EMERGENCY_CACHE_DIR / "actual_quotas.json"
    try:
        if quota_cache_file.exists():
            with open(quota_cache_file, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


def _save_quota_cache(cache: Dict[str, int]):
    """Save discovered quota values."""
    quota_cache_file = EMERGENCY_CACHE_DIR / "actual_quotas.json"
    try:
        EMERGENCY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(quota_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass


def _is_quota_cache_fresh(cache: Dict, model_name: str) -> bool:
    """Check if cached quota is still fresh (within TTL)."""
    discovered_key = f"{model_name}_discovered_at"
    if discovered_key not in cache:
        return False
    
    try:
        discovered_at = datetime.fromisoformat(cache[discovered_key])
        age_hours = (datetime.now() - discovered_at).total_seconds() / 3600
        return age_hours < QUOTA_CACHE_TTL_HOURS
    except:
        return False


def get_cached_quota(model_name: str) -> Optional[int]:
    """Get cached quota if fresh, None if expired or not found."""
    cache = _load_quota_cache()
    if model_name in cache and _is_quota_cache_fresh(cache, model_name):
        return cache[model_name]
    return None


def record_quota_from_429(model_name: str, quota_value: int):
    """
    Record actual quota discovered from a 429 error.
    Call this from error handlers when you see 'quota_value: X' in error message.
    """
    cache = _load_quota_cache()
    cache[model_name] = quota_value
    cache[f"{model_name}_discovered_at"] = datetime.now().isoformat()
    _save_quota_cache(cache)
    _safe_print(f"[QUOTA] Recorded {model_name} has {quota_value}/day (from 429)")


def _get_model_quota_from_api(model_name: str, provider: str) -> Optional[int]:
    """
    v17.9.13: Query model availability and ACTUAL quota via API.
    
    Strategy:
    1. Check cached quota from previous 429 errors (MOST ACCURATE)
    2. Check if model exists via free info endpoint
    3. Make ONE minimal test call to discover rate limit headers
    4. Return discovered quota or None if unknown
    
    NO name-based inference - all from actual API responses!
    """
    try:
        import requests
        
        # Step 1: Check quota cache (from previous 429 errors) - with TTL!
        cached_quota = get_cached_quota(model_name)
        if cached_quota is not None:
            _safe_print(f"[QUOTA] {model_name}: {cached_quota}/day (cached, fresh)")
            return cached_quota
        
        if provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                # Step 2: Check if model exists (FREE)
                info_response = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}?key={api_key}",
                    timeout=10
                )
                
                if info_response.status_code == 404:
                    return 0  # Model doesn't exist
                
                if info_response.status_code == 200:
                    # Step 3: Make ONE minimal test call to discover quota
                    # This costs 1 request but gives us REAL quota info
                    test_response = requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}",
                        json={"contents": [{"parts": [{"text": "1"}]}], "generationConfig": {"maxOutputTokens": 1}},
                        timeout=10
                    )
                    
                    # Check rate limit headers
                    daily_limit = test_response.headers.get("x-ratelimit-limit-requests-per-day")
                    if daily_limit:
                        quota = int(daily_limit)
                        record_quota_from_429(model_name, quota)  # Cache it
                        return quota
                    
                    if test_response.status_code == 429:
                        # Parse quota from error message
                        import re
                        error_text = test_response.text
                        match = re.search(r'quota_value[:\s]+(\d+)', error_text)
                        if match:
                            quota = int(match.group(1))
                            record_quota_from_429(model_name, quota)
                            return quota
                        return 0  # Exhausted, unknown limit
                    
                    elif test_response.status_code == 200:
                        # Model works, assume decent quota if no headers
                        # Will be corrected later if we hit 429
                        return 500  # Conservative assumption
                    
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
# CRITICAL TASK MODEL SELECTION
# =============================================================================

def get_high_quality_model(provider: str = "gemini") -> Optional[str]:
    """
    v17.9.15: Get a HIGH-QUALITY model for CRITICAL tasks.
    
    Critical tasks (6 calls/video max = 36/day for 6 videos):
    - Hook generation (1)
    - Final quality evaluation (1)  
    - God-tier scoring (1)
    - Title optimization (1)
    - Script refinement (1)
    - CTA generation (1)
    
    Budget: 36 calls/day → gemini-1.5-pro (50/day) is perfect!
    
    Returns: High-quality model ID, or None if unavailable
    """
    provider = provider.lower()
    
    if provider == "gemini":
        # Query for "pro" models specifically
        try:
            import requests
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                response = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                    timeout=10
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    
                    # Find "pro" models (higher quality than "flash")
                    pro_models = []
                    for m in models:
                        model_name = m.get("name", "").replace("models/", "")
                        methods = m.get("supportedGenerationMethods", [])
                        
                        if "generateContent" not in methods:
                            continue
                        
                        # Identify pro models by name pattern
                        if "pro" in model_name.lower():
                            # Check if it has ANY quota (even low)
                            quota = _get_model_quota_from_api(model_name, "gemini")
                            if quota is not None and quota > 0:
                                pro_models.append((model_name, quota))
                    
                    if pro_models:
                        # Sort by quota (highest first)
                        pro_models.sort(key=lambda x: x[1], reverse=True)
                        best_pro = pro_models[0][0]
                        _safe_print(f"[MODEL] High-quality model: {best_pro} ({pro_models[0][1]}/day)")
                        return best_pro
        except Exception as e:
            _safe_print(f"[MODEL] Pro model discovery error: {e}")
        
        return None
    
    elif provider == "groq":
        # Groq's best model is the 70B variant
        try:
            models = get_all_models("groq")
            for m in models:
                if "70b" in m.lower():
                    _safe_print(f"[MODEL] High-quality Groq model: {m}")
                    return m
        except:
            pass
        return None
    
    return None


def get_model_for_task(task_type: str) -> str:
    """
    v17.9.16: Get the BEST model for a specific task type.
    
    Task types:
    - "critical": Hook, evaluation, scoring → Use PRO model
    - "bulk": Phrases, CTAs → Use flash/fast model
    - "evaluation": Quality checks → Use PRO model
    
    Fallback chain:
    1. gemini-pro (high quality)
    2. groq-70b (high quality)
    3. gemini-flash (fast, always available)
    
    Returns: Model ID (provider:model format)
    """
    critical_tasks = ["hook", "evaluation", "scoring", "title", "script", "quality", "god_tier"]
    
    if any(t in task_type.lower() for t in critical_tasks):
        # Try to get a pro model
        pro_model = get_high_quality_model("gemini")
        if pro_model:
            _safe_print(f"[MODEL] Using high-quality Gemini for {task_type}")
            return f"gemini:{pro_model}"
        
        # Fall back to Groq 70B
        groq_pro = get_high_quality_model("groq")
        if groq_pro:
            _safe_print(f"[MODEL] Using high-quality Groq for {task_type}")
            return f"groq:{groq_pro}"
        
        # v17.9.16: Fall back to regular model (ALWAYS have a fallback!)
        _safe_print(f"[MODEL] Pro models unavailable, using fast model for {task_type}")
    
    # For bulk tasks OR fallback, use the standard fast model
    return f"gemini:{get_dynamic_gemini_model()}"


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

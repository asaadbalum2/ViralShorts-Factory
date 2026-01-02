#!/usr/bin/env python3
"""
v17.9.2: Dynamic Gemini Model Helper
=====================================

NO HARDCODING - discovers models dynamically from API.
"""

import os
import json
from pathlib import Path


def get_dynamic_gemini_model() -> str:
    """
    v17.9.2: Get the best available Gemini model dynamically.
    
    Priority:
    1. Use quota_optimizer if available (has caching and smart selection)
    2. Check local cache of available models
    3. Query API directly to discover models
    """
    
    # Try 1: Use quota_optimizer (preferred)
    try:
        from src.quota.quota_optimizer import get_best_gemini_model
        return get_best_gemini_model()
    except ImportError:
        pass
    
    # Try 2: Check cached models from previous discovery
    cache_path = Path("cache/gemini_models.json")
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                if data.get("models"):
                    return data["models"][0]
        except:
            pass
    
    # Try 3: Query API to discover available models
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
                # Filter for generative models
                generative_models = [
                    m["name"].replace("models/", "") 
                    for m in models_data.get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                if generative_models:
                    # Cache for future use
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, 'w') as f:
                        json.dump({"models": generative_models}, f)
                    return generative_models[0]
    except:
        pass
    
    # Last resort: return a commonly available model name
    # This is only reached if ALL discovery methods fail
    return "gemini-pro"  # Most stable fallback

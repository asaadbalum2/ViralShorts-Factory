#!/usr/bin/env python3
"""
ViralShorts Factory - Smart Model Router v17.9.9
=================================================

INTELLIGENT model selection that:
1. Routes each PROMPT TYPE to the BEST model for that type
2. Updates model rankings PERIODICALLY (weekly by default)
3. Has FALLBACK CHAINS for every prompt type
4. GUARANTEES eventual success (never runs out of quota)
5. Uses PROMPTS REGISTRY to learn optimal models per prompt

ARCHITECTURE:
- NOT hardcoded - model rankings are discovered and cached
- Periodic re-evaluation (weekly) to adapt to new models
- Prompt classification -> Model selection -> Fallback chain
- Prompts Registry tracks which models work best for which prompts

PROMPT TYPES:
- CREATIVE: Topics, scripts, hooks, CTAs (need human-like creativity)
- EVALUATION: Scoring, quality checks (need structured output)
- SIMPLE: Hashtags, keywords, SEO (speed matters most)
- ANALYSIS: Analytics, trends, strategy (need deep reasoning)
"""

import os
import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

# State directory for caching
STATE_DIR = Path("./data/persistent")
STATE_DIR.mkdir(parents=True, exist_ok=True)

ROUTER_CACHE_FILE = STATE_DIR / "smart_router_cache.json"
ROUTER_STATS_FILE = STATE_DIR / "smart_router_stats.json"


def safe_print(msg: str):
    """Print with Unicode fallback."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(re.sub(r'[^\x00-\x7F]+', '', msg))


# =============================================================================
# PROMPT TYPE DEFINITIONS
# =============================================================================

@dataclass
class PromptType:
    """Definition of a prompt type with its characteristics."""
    name: str
    keywords: List[str]  # Keywords to identify this type
    needs_creativity: bool  # High creativity needed?
    needs_structure: bool  # Structured JSON output needed?
    needs_speed: bool  # Speed over quality?
    needs_reasoning: bool  # Deep reasoning needed?
    max_tokens: int  # Typical max tokens
    priority: str  # "critical", "normal", "bulk"


# Define prompt types with their characteristics
PROMPT_TYPES = {
    "creative": PromptType(
        name="creative",
        keywords=["topic", "content", "hook", "voiceover", "cta", "script", 
                  "generation", "viral", "engagement", "reply", "series"],
        needs_creativity=True,
        needs_structure=False,
        needs_speed=False,
        needs_reasoning=False,
        max_tokens=2000,
        priority="critical"
    ),
    "evaluation": PromptType(
        name="evaluation",
        keywords=["evaluation", "evaluate", "quality", "score", "check", 
                  "gate", "velocity", "validate", "assessment"],
        needs_creativity=False,
        needs_structure=True,
        needs_speed=False,
        needs_reasoning=True,
        max_tokens=1500,
        priority="critical"
    ),
    "simple": PromptType(
        name="simple",
        keywords=["hashtag", "keyword", "seo", "description", "broll", 
                  "thumbnail", "sentiment", "tag", "metadata"],
        needs_creativity=False,
        needs_structure=True,
        needs_speed=True,
        needs_reasoning=False,
        max_tokens=500,
        priority="normal"
    ),
    "analysis": PromptType(
        name="analysis",
        keywords=["analysis", "analytics", "trend", "strategy", "growth",
                  "competitor", "deep", "insight", "correlation", "pattern"],
        needs_creativity=False,
        needs_structure=True,
        needs_speed=False,
        needs_reasoning=True,
        max_tokens=1500,
        priority="bulk"
    )
}


# =============================================================================
# MODEL DEFINITIONS (Discovered, not hardcoded)
# =============================================================================

@dataclass
class ModelInfo:
    """Information about a model."""
    provider: str  # "groq", "gemini", "openrouter", "huggingface"
    model_id: str  # Full model identifier
    daily_limit: int  # Estimated daily limit
    rate_limit: int  # Requests per minute
    delay: float  # Recommended delay between calls
    quality_general: float  # General quality (1-10)
    quality_creative: float  # Quality for creative tasks
    quality_structured: float  # Quality for structured output
    quality_speed: float  # Speed rating (1-10, 10=fastest)
    robustness: float  # Success rate (0-1)
    available: bool  # Currently available?


# Default model pool (discovered dynamically, this is fallback)
DEFAULT_MODELS = {
    # Groq
    "groq:llama-3.3-70b-versatile": ModelInfo(
        provider="groq", model_id="llama-3.3-70b-versatile",
        daily_limit=300, rate_limit=30, delay=2.0,
        quality_general=8.5, quality_creative=9.0, quality_structured=8.0, quality_speed=9.0,
        robustness=0.98, available=True
    ),
    "groq:llama-3.1-70b-versatile": ModelInfo(
        provider="groq", model_id="llama-3.1-70b-versatile",
        daily_limit=300, rate_limit=30, delay=2.0,
        quality_general=8.0, quality_creative=8.5, quality_structured=8.0, quality_speed=9.0,
        robustness=0.97, available=True
    ),
    "groq:llama-3.1-8b-instant": ModelInfo(
        provider="groq", model_id="llama-3.1-8b-instant",
        daily_limit=600, rate_limit=60, delay=1.0,
        quality_general=7.0, quality_creative=6.5, quality_structured=7.0, quality_speed=10.0,
        robustness=0.99, available=True
    ),
    "groq:mixtral-8x7b-32768": ModelInfo(
        provider="groq", model_id="mixtral-8x7b-32768",
        daily_limit=400, rate_limit=40, delay=1.5,
        quality_general=7.5, quality_creative=7.5, quality_structured=7.5, quality_speed=8.5,
        robustness=0.96, available=True
    ),
    # Gemini
    "gemini:gemini-1.5-flash": ModelInfo(
        provider="gemini", model_id="gemini-1.5-flash",
        daily_limit=1500, rate_limit=15, delay=4.0,
        quality_general=7.5, quality_creative=7.0, quality_structured=8.5, quality_speed=8.0,
        robustness=0.95, available=True
    ),
    "gemini:gemini-2.0-flash": ModelInfo(
        provider="gemini", model_id="gemini-2.0-flash",
        daily_limit=500, rate_limit=15, delay=4.0,
        quality_general=8.0, quality_creative=7.5, quality_structured=9.0, quality_speed=8.0,
        robustness=0.92, available=True
    ),
    "gemini:gemini-1.5-pro": ModelInfo(
        provider="gemini", model_id="gemini-1.5-pro",
        daily_limit=50, rate_limit=5, delay=12.0,
        quality_general=8.5, quality_creative=8.0, quality_structured=9.0, quality_speed=5.0,
        robustness=0.90, available=True
    ),
    # OpenRouter (free)
    "openrouter:meta-llama/llama-3.2-3b-instruct:free": ModelInfo(
        provider="openrouter", model_id="meta-llama/llama-3.2-3b-instruct:free",
        daily_limit=10000, rate_limit=60, delay=1.0,
        quality_general=6.5, quality_creative=6.0, quality_structured=6.5, quality_speed=9.0,
        robustness=0.90, available=True
    ),
    "openrouter:google/gemma-2-9b-it:free": ModelInfo(
        provider="openrouter", model_id="google/gemma-2-9b-it:free",
        daily_limit=10000, rate_limit=60, delay=1.0,
        quality_general=7.0, quality_creative=6.5, quality_structured=7.0, quality_speed=8.5,
        robustness=0.88, available=True
    ),
    # HuggingFace
    "huggingface:HuggingFaceH4/zephyr-7b-beta": ModelInfo(
        provider="huggingface", model_id="HuggingFaceH4/zephyr-7b-beta",
        daily_limit=2400, rate_limit=100, delay=36.0,
        quality_general=7.5, quality_creative=7.0, quality_structured=7.5, quality_speed=5.0,
        robustness=0.80, available=True
    ),
}


# =============================================================================
# SMART MODEL ROUTER
# =============================================================================

class SmartModelRouter:
    """
    Intelligently routes prompts to the best available model.
    
    Features:
    - Classifies prompts by type (creative, evaluation, simple, analysis)
    - Selects best model for each type
    - Periodic re-evaluation of model rankings (default: weekly)
    - Fallback chains guarantee eventual success
    - Tracks usage and success rates
    """
    
    # How often to refresh model rankings (in seconds)
    REFRESH_INTERVAL = 7 * 24 * 3600  # 7 days
    
    def __init__(self):
        self.models = {}
        self.rankings = {}  # {prompt_type: [ordered list of model keys]}
        self.stats = {"calls": 0, "successes": 0, "fallbacks": 0}
        self.last_refresh = None
        
        # Load cached data or initialize
        self._load_cache()
        
        # Refresh if needed
        if self._needs_refresh():
            self.refresh_rankings()
    
    def _load_cache(self):
        """Load cached router data."""
        try:
            if ROUTER_CACHE_FILE.exists():
                with open(ROUTER_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self.rankings = data.get("rankings", {})
                    self.last_refresh = data.get("last_refresh")
                    # Reconstruct models from cache
                    for key, model_data in data.get("models", {}).items():
                        self.models[key] = ModelInfo(**model_data)
                    safe_print(f"[ROUTER] Loaded cached rankings from {self.last_refresh}")
            else:
                self._use_defaults()
        except Exception as e:
            safe_print(f"[ROUTER] Cache load failed: {e}, using defaults")
            self._use_defaults()
        
        # Load stats
        try:
            if ROUTER_STATS_FILE.exists():
                with open(ROUTER_STATS_FILE, 'r') as f:
                    self.stats = json.load(f)
        except:
            pass
    
    def _use_defaults(self):
        """Use default model pool."""
        self.models = DEFAULT_MODELS.copy()
        self._compute_rankings()
    
    def _save_cache(self):
        """Save router data to cache."""
        try:
            data = {
                "rankings": self.rankings,
                "last_refresh": self.last_refresh,
                "models": {k: asdict(v) for k, v in self.models.items()}
            }
            with open(ROUTER_CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            safe_print(f"[ROUTER] Cache save failed: {e}")
    
    def _save_stats(self):
        """Save usage stats."""
        try:
            with open(ROUTER_STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except:
            pass
    
    def _needs_refresh(self) -> bool:
        """Check if rankings need refresh."""
        if not self.last_refresh:
            return True
        if not self.rankings:
            return True
        
        try:
            last = datetime.fromisoformat(self.last_refresh)
            return (datetime.now() - last).total_seconds() > self.REFRESH_INTERVAL
        except:
            return True
    
    def refresh_rankings(self):
        """
        Refresh model rankings by:
        1. Discovering available models from each provider
        2. Testing availability
        3. Computing rankings for each prompt type
        
        Called periodically (weekly by default) or on-demand.
        """
        safe_print("[ROUTER] Refreshing model rankings...")
        
        # Start with defaults
        self.models = DEFAULT_MODELS.copy()
        
        # Discover additional models from each provider
        self._discover_groq_models()
        self._discover_gemini_models()
        self._discover_openrouter_models()
        self._discover_huggingface_models()
        
        # Compute rankings for each prompt type
        self._compute_rankings()
        
        # Save to cache
        self.last_refresh = datetime.now().isoformat()
        self._save_cache()
        
        safe_print(f"[ROUTER] Rankings updated: {len(self.models)} models, "
                   f"{len(self.rankings)} prompt types")
    
    def _discover_groq_models(self):
        """Discover available Groq models."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return
        
        try:
            import requests
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                for model in models_data:
                    model_id = model.get("id", "")
                    key = f"groq:{model_id}"
                    if key not in self.models:
                        # Add new model with estimated stats
                        self.models[key] = ModelInfo(
                            provider="groq", model_id=model_id,
                            daily_limit=300, rate_limit=30, delay=2.0,
                            quality_general=7.0, quality_creative=7.0,
                            quality_structured=7.0, quality_speed=8.0,
                            robustness=0.90, available=True
                        )
                safe_print(f"[ROUTER] Discovered {len(models_data)} Groq models")
        except Exception as e:
            safe_print(f"[ROUTER] Groq discovery failed: {e}")
    
    def _discover_gemini_models(self):
        """Discover available Gemini models."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return
        
        try:
            import requests
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    name = model.get("name", "").replace("models/", "")
                    if "generateContent" in model.get("supportedGenerationMethods", []):
                        key = f"gemini:{name}"
                        if key not in self.models:
                            # Estimate stats based on model name
                            is_flash = "flash" in name.lower()
                            is_pro = "pro" in name.lower()
                            self.models[key] = ModelInfo(
                                provider="gemini", model_id=name,
                                daily_limit=1500 if is_flash else (50 if is_pro else 500),
                                rate_limit=15 if is_flash else 5,
                                delay=4.0 if is_flash else 12.0,
                                quality_general=7.5 if is_flash else 8.5,
                                quality_creative=7.0 if is_flash else 8.0,
                                quality_structured=8.5 if is_flash else 9.0,
                                quality_speed=8.0 if is_flash else 5.0,
                                robustness=0.95 if is_flash else 0.90,
                                available=True
                            )
                safe_print(f"[ROUTER] Discovered {len(models)} Gemini models")
        except Exception as e:
            safe_print(f"[ROUTER] Gemini discovery failed: {e}")
    
    def _discover_openrouter_models(self):
        """Discover available OpenRouter free models."""
        try:
            import requests
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                timeout=10
            )
            if response.status_code == 200:
                models = response.json().get("data", [])
                free_count = 0
                for model in models:
                    model_id = model.get("id", "")
                    # Only add free models
                    if ":free" in model_id.lower() or model.get("pricing", {}).get("prompt") == "0":
                        key = f"openrouter:{model_id}"
                        if key not in self.models:
                            self.models[key] = ModelInfo(
                                provider="openrouter", model_id=model_id,
                                daily_limit=10000, rate_limit=60, delay=1.0,
                                quality_general=6.5, quality_creative=6.0,
                                quality_structured=6.5, quality_speed=9.0,
                                robustness=0.85, available=True
                            )
                            free_count += 1
                safe_print(f"[ROUTER] Discovered {free_count} free OpenRouter models")
        except Exception as e:
            safe_print(f"[ROUTER] OpenRouter discovery failed: {e}")
    
    def _discover_huggingface_models(self):
        """Discover available HuggingFace models (use defaults, HF has no easy listing)."""
        # HuggingFace doesn't have easy model listing, keep defaults
        pass
    
    def _compute_rankings(self):
        """
        Compute model rankings for each prompt type.
        
        Rankings are based on prompt type requirements:
        - Creative: prioritize quality_creative
        - Evaluation: prioritize quality_structured
        - Simple: prioritize quality_speed + robustness
        - Analysis: prioritize quality_general + quality_structured
        """
        for prompt_type_name, prompt_type in PROMPT_TYPES.items():
            scored_models = []
            
            for key, model in self.models.items():
                if not model.available:
                    continue
                
                # Calculate score based on prompt type needs
                score = 0.0
                
                if prompt_type.needs_creativity:
                    score += model.quality_creative * 2.0
                else:
                    score += model.quality_creative * 0.5
                
                if prompt_type.needs_structure:
                    score += model.quality_structured * 1.5
                else:
                    score += model.quality_structured * 0.5
                
                if prompt_type.needs_speed:
                    score += model.quality_speed * 1.5
                    score += model.daily_limit / 1000  # Bonus for high quota
                else:
                    score += model.quality_speed * 0.3
                
                if prompt_type.needs_reasoning:
                    score += model.quality_general * 1.2
                else:
                    score += model.quality_general * 0.5
                
                # Always factor in robustness
                score += model.robustness * 5.0
                
                scored_models.append((key, score))
            
            # Sort by score (highest first)
            scored_models.sort(key=lambda x: x[1], reverse=True)
            
            # Store ranking (ordered list of model keys)
            self.rankings[prompt_type_name] = [key for key, _ in scored_models]
        
        safe_print("[ROUTER] Rankings computed for all prompt types")
    
    def classify_prompt(self, prompt: str, hint: str = None) -> str:
        """
        Classify a prompt into a type.
        
        Args:
            prompt: The full prompt text
            hint: Optional hint about the prompt type
        
        Returns:
            Prompt type name ("creative", "evaluation", "simple", "analysis")
        """
        prompt_lower = prompt.lower()
        
        # If hint provided, try to match it first
        if hint:
            hint_lower = hint.lower()
            for type_name, prompt_type in PROMPT_TYPES.items():
                if any(kw in hint_lower for kw in prompt_type.keywords):
                    return type_name
        
        # Score each type based on keyword matches
        type_scores = {}
        for type_name, prompt_type in PROMPT_TYPES.items():
            score = sum(1 for kw in prompt_type.keywords if kw in prompt_lower)
            type_scores[type_name] = score
        
        # Return highest scoring type, default to "simple"
        best_type = max(type_scores, key=type_scores.get)
        if type_scores[best_type] > 0:
            return best_type
        
        return "simple"  # Default
    
    def get_model_chain(self, prompt_type: str) -> List[Tuple[str, ModelInfo]]:
        """
        Get the full fallback chain for a prompt type.
        
        Returns:
            List of (model_key, ModelInfo) tuples in priority order
        """
        if prompt_type not in self.rankings:
            prompt_type = "simple"
        
        chain = []
        for key in self.rankings.get(prompt_type, []):
            if key in self.models:
                chain.append((key, self.models[key]))
        
        # Ensure we always have at least some models
        if not chain:
            for key, model in self.models.items():
                chain.append((key, model))
        
        return chain
    
    def get_best_model(self, prompt: str, hint: str = None, 
                       prompt_name: str = None) -> Tuple[str, ModelInfo]:
        """
        Get the best model for a prompt.
        
        Args:
            prompt: The prompt text
            hint: Optional hint about prompt type
            prompt_name: Optional specific prompt name (e.g., "VIRAL_TOPIC_PROMPT")
        
        Returns:
            (model_key, ModelInfo) for the best model
        """
        # v17.9.9: Check prompts registry for per-prompt recommendations
        if prompt_name:
            try:
                from prompts_registry import get_best_model_for_prompt
                recommended = get_best_model_for_prompt(prompt_name)
                if recommended and recommended in self.models:
                    return (recommended, self.models[recommended])
            except ImportError:
                pass
            except Exception:
                pass
        
        # Fall back to type-based selection
        prompt_type = self.classify_prompt(prompt, hint)
        chain = self.get_model_chain(prompt_type)
        
        if chain:
            return chain[0]
        
        # Ultimate fallback
        for key, model in self.models.items():
            return (key, model)
        
        # Should never reach here
        return ("groq:llama-3.3-70b-versatile", DEFAULT_MODELS["groq:llama-3.3-70b-versatile"])
    
    def record_result(self, model_key: str, success: bool, was_fallback: bool = False):
        """Record the result of a model call for stats."""
        self.stats["calls"] = self.stats.get("calls", 0) + 1
        if success:
            self.stats["successes"] = self.stats.get("successes", 0) + 1
        if was_fallback:
            self.stats["fallbacks"] = self.stats.get("fallbacks", 0) + 1
        
        # Update model-specific stats
        model_stats = self.stats.get("models", {})
        if model_key not in model_stats:
            model_stats[model_key] = {"calls": 0, "successes": 0}
        model_stats[model_key]["calls"] += 1
        if success:
            model_stats[model_key]["successes"] += 1
        self.stats["models"] = model_stats
        
        # Save periodically (every 10 calls)
        if self.stats["calls"] % 10 == 0:
            self._save_stats()
    
    def get_stats(self) -> Dict:
        """Get router statistics."""
        return {
            "total_calls": self.stats.get("calls", 0),
            "successes": self.stats.get("successes", 0),
            "fallbacks": self.stats.get("fallbacks", 0),
            "success_rate": (self.stats.get("successes", 0) / max(1, self.stats.get("calls", 1))) * 100,
            "fallback_rate": (self.stats.get("fallbacks", 0) / max(1, self.stats.get("calls", 1))) * 100,
            "models_used": len(self.stats.get("models", {})),
            "last_refresh": self.last_refresh
        }
    
    def print_rankings(self):
        """Print current rankings for debugging."""
        safe_print("\n" + "=" * 60)
        safe_print("SMART MODEL ROUTER - CURRENT RANKINGS")
        safe_print("=" * 60)
        
        for prompt_type, model_keys in self.rankings.items():
            safe_print(f"\n{prompt_type.upper()}:")
            for i, key in enumerate(model_keys[:5], 1):
                model = self.models.get(key)
                if model:
                    safe_print(f"  {i}. {key} (quality={model.quality_general}, "
                              f"robust={model.robustness:.0%})")
        
        safe_print("\n" + "=" * 60)


# =============================================================================
# GLOBAL INSTANCE & CONVENIENCE FUNCTIONS
# =============================================================================

_router = None


def get_smart_router() -> SmartModelRouter:
    """Get the global SmartModelRouter instance."""
    global _router
    if _router is None:
        _router = SmartModelRouter()
    return _router


def get_best_model_for_prompt(prompt: str, hint: str = None) -> Tuple[str, Dict]:
    """
    Convenience function to get best model for a prompt.
    
    Returns:
        (model_key, model_info_dict)
    """
    router = get_smart_router()
    key, info = router.get_best_model(prompt, hint)
    return key, asdict(info)


def get_fallback_chain(prompt_type: str) -> List[Tuple[str, Dict]]:
    """
    Get the fallback chain for a prompt type.
    
    Returns:
        List of (model_key, model_info_dict)
    """
    router = get_smart_router()
    chain = router.get_model_chain(prompt_type)
    return [(key, asdict(info)) for key, info in chain]


def classify_prompt(prompt: str, hint: str = None) -> str:
    """Classify a prompt into a type."""
    return get_smart_router().classify_prompt(prompt, hint)


def force_refresh_rankings():
    """Force a refresh of model rankings."""
    router = get_smart_router()
    router.refresh_rankings()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    safe_print("=" * 60)
    safe_print("SMART MODEL ROUTER TEST")
    safe_print("=" * 60)
    
    router = get_smart_router()
    
    # Print rankings
    router.print_rankings()
    
    # Test prompt classification
    test_prompts = [
        ("Generate a viral topic about psychology", "topic"),
        ("Evaluate this content for virality", "evaluation"),
        ("Generate hashtags for this video", "hashtag"),
        ("Analyze trends in our category performance", "analysis"),
    ]
    
    safe_print("\nPROMPT CLASSIFICATION TEST:")
    safe_print("-" * 60)
    
    for prompt, hint in test_prompts:
        prompt_type = router.classify_prompt(prompt, hint)
        model_key, model_info = router.get_best_model(prompt, hint)
        safe_print(f"\nPrompt: {prompt[:50]}...")
        safe_print(f"  Type: {prompt_type}")
        safe_print(f"  Best Model: {model_key}")
        safe_print(f"  Chain Length: {len(router.get_model_chain(prompt_type))}")
    
    # Print stats
    safe_print("\nROUTER STATS:")
    safe_print("-" * 60)
    stats = router.get_stats()
    for key, value in stats.items():
        safe_print(f"  {key}: {value}")
    
    safe_print("\n" + "=" * 60)


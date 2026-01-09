#!/usr/bin/env python3
"""
Aggressive Mode Controller
==========================

v1.0: Implements the "Aggressive Mode" switch for maximizing quota usage.

When ENABLED:
- Uses ALL available "bonus" quota for extra analytics
- Runs virality analysis more frequently
- Runs self-learning more aggressively  
- Generates research videos (metadata only, no upload)
- Maximizes model throughput utilization

When DISABLED (default):
- Normal operation, conservative quota usage
- Only essential API calls made
- Standard daily schedule

Usage:
    from src.core.aggressive_mode import AggressiveMode
    
    # Check mode
    if AggressiveMode.is_enabled():
        run_extra_analytics()
    
    # Enable/disable
    AggressiveMode.enable()
    AggressiveMode.disable()
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# State file location
STATE_FILE = Path("data/persistent/aggressive_mode.json")


class AggressiveMode:
    """
    Aggressive Mode controller for maximizing quota usage.
    
    This is a SWITCH - when on, the system uses all available quota
    for extra analytics, learning, and research.
    """
    
    # Default state
    _state: Dict = {
        "enabled": False,
        "enabled_at": None,
        "disabled_at": None,
        "auto_disable_after_hours": 24,  # Auto-disable after 24h to prevent quota waste
        "features": {
            "extra_virality_analysis": True,
            "aggressive_self_learning": True,
            "research_video_generation": True,  # Generate but don't upload
            "bonus_quota_usage": True,
            "frequent_competitor_analysis": True,
        },
        "stats": {
            "extra_api_calls_made": 0,
            "research_videos_generated": 0,
            "virality_analyses_run": 0,
            "self_learning_cycles": 0,
        }
    }
    
    @classmethod
    def _load_state(cls) -> Dict:
        """Load state from persistent storage."""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r') as f:
                    saved = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    cls._state.update(saved)
                    
                    # Check auto-disable
                    if cls._state.get("enabled") and cls._state.get("enabled_at"):
                        enabled_at = datetime.fromisoformat(cls._state["enabled_at"])
                        hours_enabled = (datetime.now() - enabled_at).total_seconds() / 3600
                        auto_hours = cls._state.get("auto_disable_after_hours", 24)
                        
                        if hours_enabled > auto_hours:
                            print(f"[AGGRESSIVE] Auto-disabled after {hours_enabled:.1f}h")
                            cls._state["enabled"] = False
                            cls._state["disabled_at"] = datetime.now().isoformat()
                            cls._save_state()
        except Exception as e:
            print(f"[AGGRESSIVE] Failed to load state: {e}")
        
        return cls._state
    
    @classmethod
    def _save_state(cls):
        """Save state to persistent storage."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump(cls._state, f, indent=2)
        except Exception as e:
            print(f"[AGGRESSIVE] Failed to save state: {e}")
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if aggressive mode is enabled."""
        cls._load_state()
        return cls._state.get("enabled", False)
    
    @classmethod
    def enable(cls, auto_disable_hours: int = 24):
        """
        Enable aggressive mode.
        
        Args:
            auto_disable_hours: Auto-disable after this many hours (default 24)
        """
        cls._load_state()
        cls._state["enabled"] = True
        cls._state["enabled_at"] = datetime.now().isoformat()
        cls._state["auto_disable_after_hours"] = auto_disable_hours
        cls._save_state()
        print(f"[AGGRESSIVE] MODE ENABLED - will auto-disable in {auto_disable_hours}h")
        print(f"[AGGRESSIVE] Extra features: {list(cls._state['features'].keys())}")
    
    @classmethod
    def disable(cls):
        """Disable aggressive mode."""
        cls._load_state()
        cls._state["enabled"] = False
        cls._state["disabled_at"] = datetime.now().isoformat()
        cls._save_state()
        print(f"[AGGRESSIVE] MODE DISABLED")
        print(f"[AGGRESSIVE] Stats: {cls._state['stats']}")
    
    @classmethod
    def is_feature_enabled(cls, feature: str) -> bool:
        """Check if a specific aggressive feature is enabled."""
        if not cls.is_enabled():
            return False
        return cls._state.get("features", {}).get(feature, False)
    
    @classmethod
    def record_activity(cls, activity_type: str, count: int = 1):
        """Record aggressive mode activity for stats."""
        cls._load_state()
        if activity_type in cls._state["stats"]:
            cls._state["stats"][activity_type] += count
            cls._save_state()
    
    @classmethod
    def get_stats(cls) -> Dict:
        """Get aggressive mode statistics."""
        cls._load_state()
        return cls._state.get("stats", {})
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get full status report."""
        cls._load_state()
        status = {
            "enabled": cls._state.get("enabled", False),
            "enabled_at": cls._state.get("enabled_at"),
            "features": cls._state.get("features", {}),
            "stats": cls._state.get("stats", {}),
        }
        
        if status["enabled"] and status["enabled_at"]:
            enabled_at = datetime.fromisoformat(status["enabled_at"])
            hours_active = (datetime.now() - enabled_at).total_seconds() / 3600
            auto_hours = cls._state.get("auto_disable_after_hours", 24)
            status["hours_active"] = round(hours_active, 1)
            status["hours_remaining"] = round(max(0, auto_hours - hours_active), 1)
        
        return status


def get_bonus_models() -> List[Dict]:
    """
    Get bonus quota models for aggressive mode.
    
    These are models with quota that would be wasted if not used.
    """
    try:
        from src.ai.model_helper import categorize_models_for_usage, _discover_gemini_models
        from src.ai.model_helper import get_model_quality_score, _is_model_usable
        
        # Get all Gemini models
        models = _discover_gemini_models()
        
        # Score and categorize
        models_with_info = []
        for model in models:
            is_usable, quota = _is_model_usable(model, "gemini")
            if is_usable:
                score = get_model_quality_score(model)
                models_with_info.append((model, quota, score, {}))
        
        # Get categorization
        categories = categorize_models_for_usage(models_with_info)
        
        # Return bonus models (extra quota we can use)
        bonus = categories.get("bonus", [])
        
        # If no explicit bonus category, look for backup models
        if not bonus:
            bonus = categories.get("backup", [])
        
        return bonus
        
    except Exception as e:
        print(f"[AGGRESSIVE] Failed to get bonus models: {e}")
        return []


def calculate_available_bonus_quota() -> Dict:
    """
    Calculate how much bonus quota is available for aggressive mode.
    
    Returns:
        Dict with quota breakdown by provider
    """
    try:
        # Import model helpers
        from src.ai.model_helper import MODEL_RATE_LIMITS
        
        # Get bonus models
        bonus_models = get_bonus_models()
        
        total_bonus_quota = sum(m.get("quota", 0) for m in bonus_models)
        
        # Standard production needs (6 videos/day)
        production_needs = {
            "video_generation": 6 * 15,  # 15 calls per video
            "analytics": 20,
            "total": 110
        }
        
        return {
            "bonus_quota_available": total_bonus_quota,
            "production_needs": production_needs["total"],
            "free_for_aggressive": max(0, total_bonus_quota - production_needs["total"]),
            "bonus_models_count": len(bonus_models),
        }
        
    except Exception as e:
        print(f"[AGGRESSIVE] Failed to calculate bonus quota: {e}")
        return {"bonus_quota_available": 0, "free_for_aggressive": 0}


class AggressiveFeatures:
    """
    Collection of aggressive mode features.
    """
    
    @staticmethod
    def run_extra_virality_analysis():
        """Run additional virality analysis using bonus quota."""
        if not AggressiveMode.is_feature_enabled("extra_virality_analysis"):
            return None
        
        try:
            # Import virality engine
            from src.analytics.virality_engine import ViralityEngine
            
            engine = ViralityEngine()
            results = engine.analyze_trending_patterns()
            
            AggressiveMode.record_activity("virality_analyses_run")
            print("[AGGRESSIVE] Extra virality analysis completed")
            
            return results
        except Exception as e:
            print(f"[AGGRESSIVE] Virality analysis failed: {e}")
            return None
    
    @staticmethod
    def run_aggressive_self_learning():
        """Run additional self-learning cycles."""
        if not AggressiveMode.is_feature_enabled("aggressive_self_learning"):
            return None
        
        try:
            # Import self-learning engine
            from src.analytics.self_learning import SelfLearningEngine
            
            engine = SelfLearningEngine()
            results = engine.run_learning_cycle()
            
            AggressiveMode.record_activity("self_learning_cycles")
            print("[AGGRESSIVE] Extra self-learning cycle completed")
            
            return results
        except Exception as e:
            print(f"[AGGRESSIVE] Self-learning failed: {e}")
            return None
    
    @staticmethod
    def generate_research_video(topic: str = None):
        """
        Generate a research video (metadata only, no upload).
        
        This uses bonus quota to test content ideas without
        consuming YouTube upload quota.
        """
        if not AggressiveMode.is_feature_enabled("research_video_generation"):
            return None
        
        try:
            # Import video generator
            from pro_video_generator import VideoGenerator
            
            generator = VideoGenerator()
            
            # Generate video metadata only (no render, no upload)
            result = generator.generate_concept(
                research_mode=True,  # Flag to not upload
                topic=topic
            )
            
            AggressiveMode.record_activity("research_videos_generated")
            print("[AGGRESSIVE] Research video concept generated")
            
            return result
        except Exception as e:
            print(f"[AGGRESSIVE] Research video failed: {e}")
            return None


# CLI interface
def main():
    """Command line interface for aggressive mode."""
    import sys
    
    if len(sys.argv) < 2:
        # Show status
        status = AggressiveMode.get_status()
        print("\n=== AGGRESSIVE MODE STATUS ===")
        print(f"Enabled: {'YES' if status['enabled'] else 'NO'}")
        if status['enabled']:
            print(f"Active for: {status.get('hours_active', 0)}h")
            print(f"Auto-disable in: {status.get('hours_remaining', 0)}h")
        print(f"\nFeatures: {list(status.get('features', {}).keys())}")
        print(f"Stats: {status.get('stats', {})}")
        
        # Show bonus quota
        quota = calculate_available_bonus_quota()
        print(f"\nBonus Quota Available: {quota.get('bonus_quota_available', 0)}")
        print(f"Free for Aggressive: {quota.get('free_for_aggressive', 0)}")
        return
    
    command = sys.argv[1].lower()
    
    if command in ["on", "enable", "start"]:
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        AggressiveMode.enable(hours)
        
    elif command in ["off", "disable", "stop"]:
        AggressiveMode.disable()
        
    elif command in ["status", "info"]:
        status = AggressiveMode.get_status()
        print(json.dumps(status, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        print("Usage: python aggressive_mode.py [on|off|status]")


if __name__ == "__main__":
    main()

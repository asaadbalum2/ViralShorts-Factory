#!/usr/bin/env python3
"""
ViralShorts Factory - Self-Learning Engine v15.0
=================================================

This module implements an AI-driven self-learning system that:
1. Tracks successful patterns from high-scoring videos
2. Learns from failures to avoid repeating mistakes
3. Adapts prompts based on what works
4. Provides real-time recommendations for content generation

The goal: Every video gets BETTER than the last!

Data Sources:
- Video metadata and scores from analytics_feedback.py
- First-attempt quality history from token_budget_manager.py
- Persistent state from GitHub Artifacts

Learning Strategy:
1. Score-based learning: What patterns correlate with high scores?
2. Engagement-based learning: What patterns get more views/likes?
3. Regeneration avoidance: What patterns avoid regenerations?
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re

# State directory
STATE_DIR = Path("data/persistent")
STATE_DIR.mkdir(parents=True, exist_ok=True)

LEARNING_FILE = STATE_DIR / "self_learning.json"


@dataclass
class LearningPattern:
    """A pattern learned from video performance."""
    pattern_type: str  # "hook", "topic", "category", "phrase_style", "number_format"
    pattern_value: str  # The actual pattern
    success_count: int
    failure_count: int
    avg_score: float
    last_used: str
    examples: List[str]


class SelfLearningEngine:
    """
    Self-learning engine that improves video quality over time.
    
    Learns from:
    - High-scoring videos (8+/10)
    - Low-scoring videos (<6/10)
    - Regeneration patterns
    - View/engagement data
    """
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Load learning data from disk."""
        try:
            if LEARNING_FILE.exists():
                with open(LEARNING_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[SelfLearning] Load error: {e}")
        
        return {
            "patterns": {
                "hooks": [],      # Successful hook patterns
                "topics": [],     # Topic patterns that work
                "categories": [], # Best performing categories
                "phrases": [],    # Phrase styles that score high
                "numbers": [],    # Number formats that feel real
                "failures": [],   # Patterns to avoid
            },
            "stats": {
                "total_videos": 0,
                "avg_first_attempt_score": 5.0,
                "regeneration_rate": 0.5,
                "top_categories": [],
                "worst_categories": [],
            },
            "recommendations": {
                "boost_phrases": [],     # Phrases that improve scores
                "avoid_phrases": [],     # Phrases that hurt scores
                "best_hook_styles": [],  # Hook patterns that work
                "optimal_length": 4,     # Best phrase count
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _save(self):
        """Save learning data to disk."""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(LEARNING_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[SelfLearning] Save error: {e}")
    
    def learn_from_video(self, 
                          score: int, 
                          category: str, 
                          topic: str,
                          hook: str, 
                          phrases: List[str],
                          was_regeneration: bool = False):
        """
        Learn from a generated video.
        
        Args:
            score: Quality score (1-10)
            category: Video category
            topic: Specific topic
            hook: First phrase (hook)
            phrases: All phrases
            was_regeneration: True if this was a regeneration
        """
        # Update stats
        self.data["stats"]["total_videos"] += 1
        
        # Extract patterns
        hook_pattern = self._extract_hook_pattern(hook)
        number_patterns = self._extract_number_patterns(phrases)
        phrase_style = self._analyze_phrase_style(phrases)
        
        if score >= 8:
            # SUCCESS - Learn what works
            self._record_success("hooks", hook_pattern, hook[:50])
            self._record_success("categories", category, topic[:30])
            self._record_success("phrases", phrase_style, hook[:50])
            for np in number_patterns:
                self._record_success("numbers", np["type"], np["example"])
            
            # Update best categories
            if category not in self.data["stats"]["top_categories"]:
                self.data["stats"]["top_categories"].append(category)
                self.data["stats"]["top_categories"] = self.data["stats"]["top_categories"][-10:]
                
        elif score < 6:
            # FAILURE - Learn what to avoid
            self._record_failure("failures", hook_pattern, hook[:50])
            self._record_failure("failures", category, topic[:30])
            
            # Update worst categories
            if category not in self.data["stats"]["worst_categories"]:
                self.data["stats"]["worst_categories"].append(category)
                self.data["stats"]["worst_categories"] = self.data["stats"]["worst_categories"][-5:]
        
        # Update regeneration rate
        if was_regeneration:
            total = self.data["stats"]["total_videos"]
            old_rate = self.data["stats"]["regeneration_rate"]
            self.data["stats"]["regeneration_rate"] = (
                (old_rate * (total - 1) + 1.0) / total
            )
        
        # Update recommendations based on learning
        self._update_recommendations()
        
        self._save()
        print(f"[SelfLearning] Learned from video: score={score}, category={category}")
    
    def _extract_hook_pattern(self, hook: str) -> str:
        """Extract the pattern type from a hook."""
        hook_lower = hook.lower()
        
        if '?' in hook:
            return "question"
        elif any(word in hook_lower for word in ["stop", "wait", "hold on", "listen"]):
            return "pattern_interrupt"
        elif any(word in hook_lower for word in ["99%", "most people", "nobody", "everyone"]):
            return "social_proof"
        elif any(word in hook_lower for word in ["secret", "truth", "hidden", "won't tell"]):
            return "mystery"
        elif any(word in hook_lower for word in ["shocking", "unbelievable", "crazy", "insane"]):
            return "shock"
        elif re.search(r'\$\d+|^\d+%|\d+ (times|days|hours)', hook_lower):
            return "specific_number"
        else:
            return "statement"
    
    def _extract_number_patterns(self, phrases: List[str]) -> List[Dict]:
        """Extract number patterns from phrases."""
        patterns = []
        full_text = " ".join(phrases)
        
        # Round numbers like $500, 80%, 1000
        if re.search(r'\$\d+00\b|\b\d0%\b|\b\d+000\b', full_text):
            patterns.append({"type": "round_number", "example": re.findall(r'\$\d+00|\d0%|\d+000', full_text)[0]})
        
        # Specific believable numbers like 3x, 10 minutes, 5 steps
        if re.search(r'\b\d+x\b|\b\d+ (minutes?|hours?|steps?|days?)\b', full_text):
            match = re.findall(r'\d+x|\d+ (?:minutes?|hours?|steps?|days?)', full_text)
            if match:
                patterns.append({"type": "contextual_number", "example": match[0]})
        
        # Awkward numbers (to avoid)
        if re.search(r'\$\d{4,}\b|\d+\.\d+%', full_text):
            patterns.append({"type": "awkward_number", "example": "AVOID"})
        
        return patterns
    
    def _analyze_phrase_style(self, phrases: List[str]) -> str:
        """Analyze the overall phrase style."""
        avg_length = sum(len(p.split()) for p in phrases) / len(phrases) if phrases else 0
        
        if avg_length <= 8:
            return "punchy"
        elif avg_length <= 12:
            return "concise"
        else:
            return "verbose"
    
    def _record_success(self, pattern_type: str, pattern_value: str, example: str):
        """Record a successful pattern."""
        patterns = self.data["patterns"].get(pattern_type, [])
        
        # Find existing or create new
        existing = next((p for p in patterns if p.get("value") == pattern_value), None)
        
        if existing:
            existing["success_count"] = existing.get("success_count", 0) + 1
            existing["last_used"] = datetime.now().isoformat()
            if example not in existing.get("examples", []):
                existing["examples"] = (existing.get("examples", []) + [example])[-5:]
        else:
            patterns.append({
                "value": pattern_value,
                "success_count": 1,
                "failure_count": 0,
                "last_used": datetime.now().isoformat(),
                "examples": [example]
            })
        
        # Keep only top patterns
        patterns.sort(key=lambda x: x.get("success_count", 0), reverse=True)
        self.data["patterns"][pattern_type] = patterns[:20]
    
    def _record_failure(self, pattern_type: str, pattern_value: str, example: str):
        """Record a failed pattern."""
        patterns = self.data["patterns"].get(pattern_type, [])
        
        existing = next((p for p in patterns if p.get("value") == pattern_value), None)
        
        if existing:
            existing["failure_count"] = existing.get("failure_count", 0) + 1
            existing["last_used"] = datetime.now().isoformat()
        else:
            patterns.append({
                "value": pattern_value,
                "success_count": 0,
                "failure_count": 1,
                "last_used": datetime.now().isoformat(),
                "examples": [example]
            })
        
        self.data["patterns"][pattern_type] = patterns[:20]
    
    def _update_recommendations(self):
        """Update recommendations based on learned patterns."""
        # Best hook styles
        hooks = self.data["patterns"].get("hooks", [])
        self.data["recommendations"]["best_hook_styles"] = [
            h["value"] for h in hooks 
            if h.get("success_count", 0) >= 2
        ][:5]
        
        # Phrases to boost
        phrases = self.data["patterns"].get("phrases", [])
        self.data["recommendations"]["boost_phrases"] = [
            p["value"] for p in phrases 
            if p.get("success_count", 0) >= 2
        ][:5]
        
        # Phrases to avoid
        failures = self.data["patterns"].get("failures", [])
        self.data["recommendations"]["avoid_phrases"] = [
            f["value"] for f in failures 
            if f.get("failure_count", 0) >= 2
        ][:5]
    
    def get_prompt_boost(self) -> str:
        """Get prompt boost based on learning."""
        boost = """
=== SELF-LEARNING INSIGHTS ===
Based on analysis of our best-performing videos:

"""
        # Best hook styles
        if self.data["recommendations"]["best_hook_styles"]:
            boost += "BEST HOOK PATTERNS (use these!):\n"
            for style in self.data["recommendations"]["best_hook_styles"][:3]:
                boost += f"- {style}\n"
            boost += "\n"
        
        # Top categories
        if self.data["stats"]["top_categories"]:
            boost += f"TOP CATEGORIES: {', '.join(self.data['stats']['top_categories'][:5])}\n\n"
        
        # Things to avoid
        if self.data["recommendations"]["avoid_phrases"]:
            boost += "AVOID THESE (caused failures):\n"
            for phrase in self.data["recommendations"]["avoid_phrases"][:3]:
                boost += f"- {phrase}\n"
            boost += "\n"
        
        # Stats
        boost += f"""
PERFORMANCE STATS:
- Total videos analyzed: {self.data['stats']['total_videos']}
- Regeneration rate: {self.data['stats']['regeneration_rate']*100:.1f}%
- Goal: <10% regeneration rate
================================
"""
        return boost
    
    def should_avoid_category(self, category: str) -> bool:
        """Check if a category should be avoided."""
        return category in self.data["stats"]["worst_categories"]
    
    def get_recommended_categories(self) -> List[str]:
        """Get recommended categories based on learning."""
        return self.data["stats"]["top_categories"][:5]


# Singleton instance
_learning_engine = None

def get_learning_engine() -> SelfLearningEngine:
    """Get the singleton learning engine."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = SelfLearningEngine()
    return _learning_engine


if __name__ == "__main__":
    # Test the learning engine
    engine = get_learning_engine()
    
    # Simulate some learning
    engine.learn_from_video(
        score=9,
        category="productivity",
        topic="Morning routines that work",
        hook="STOP - This simple habit changed my life",
        phrases=[
            "STOP - This simple habit changed my life",
            "Wake up 30 minutes earlier every day",
            "You'll get 3x more done before noon",
            "Comment if you'll try this tomorrow!"
        ]
    )
    
    engine.learn_from_video(
        score=4,
        category="crypto",
        topic="Bitcoin price prediction",
        hook="You're losing $3333 every year",
        phrases=[
            "You're losing $3333 every year",
            "Crypto fees are killing your profits",
            "Use this obscure exchange instead"
        ],
        was_regeneration=True
    )
    
    print("\n" + engine.get_prompt_boost())


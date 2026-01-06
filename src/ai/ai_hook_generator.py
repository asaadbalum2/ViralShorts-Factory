#!/usr/bin/env python3
"""
ViralShorts Factory - AI Hook Generator v17.8
==============================================

Generates scroll-stopping hooks using AI.

Hooks are THE most important part of a short video:
- First 0.5-1.5 seconds determine if viewer stays
- Must create curiosity gap
- Must promise value
- Must stop the scroll

This module:
1. Uses AI to generate hooks based on topic/category
2. Learns from hook performance
3. Generates variations for A/B testing
"""

import os
from src.ai.model_helper import get_dynamic_gemini_model
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def safe_print(msg: str):
    """Print with Unicode fallback."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(re.sub(r'[^\x00-\x7F]+', '', msg))


STATE_DIR = Path("./data/persistent")
STATE_DIR.mkdir(parents=True, exist_ok=True)

HOOK_PERFORMANCE_FILE = STATE_DIR / "hook_performance.json"


class AIHookGenerator:
    """
    Generates viral hooks using AI and learns from performance.
    """
    
    def __init__(self):
        self.data = self._load()
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
    
    def _load(self) -> Dict:
        try:
            if HOOK_PERFORMANCE_FILE.exists():
                with open(HOOK_PERFORMANCE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "generated_hooks": [],  # All hooks we've generated
            "performance": {},      # hook_hash -> {views, likes, ctr}
            "best_patterns": [],    # Patterns that work
            "worst_patterns": [],   # Patterns to avoid
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(HOOK_PERFORMANCE_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def generate_hook(self, topic: str, category: str, 
                     style: str = "auto") -> str:
        """
        Generate a scroll-stopping hook for a topic.
        
        Args:
            topic: The video topic
            category: Content category (psychology, money, etc.)
            style: Hook style (question, statement, challenge, pattern_interrupt, auto)
        
        Returns:
            The generated hook text
        """
        # First try: Get from learned best patterns
        learned_hook = self._try_learned_pattern(topic, category)
        if learned_hook:
            safe_print(f"   [HOOK] Using learned pattern")
            return learned_hook
        
        # Second try: Generate with AI
        ai_hook = self._generate_with_ai(topic, category, style)
        if ai_hook:
            safe_print(f"   [HOOK] AI-generated hook")
            return ai_hook
        
        # Fallback: Simple template
        return self._fallback_hook(topic, category)
    
    def _try_learned_pattern(self, topic: str, category: str) -> Optional[str]:
        """
        v17.9.15: Apply learned best-performing patterns from analytics.
        
        Uses real performance data to create hooks with proven patterns.
        """
        if not self.data.get("best_patterns"):
            return None
        
        # Need at least 3 successful patterns to have confidence
        best_patterns = self.data.get("best_patterns", [])
        if len(best_patterns) < 3:
            return None
        
        # Get pattern performance data
        performance = self.data.get("performance", {})
        
        # Find patterns with high engagement
        high_performers = []
        for hook_hash, perf in performance.items():
            if perf.get("views", 0) > 1000 or perf.get("ctr", 0) > 0.05:
                high_performers.append(perf)
        
        if not high_performers:
            return None
        
        # Analyze successful hooks to find common patterns
        import random
        
        # v17.9.15: Use AI to adapt proven patterns to new topic
        try:
            best_hook_examples = [p.get("hook", "") for p in high_performers if p.get("hook")][:3]
            if best_hook_examples:
                # Use AI to create variation based on successful patterns
                prompt = f"""Based on these PROVEN viral hooks:
{chr(10).join(f'- "{h}"' for h in best_hook_examples)}

Create a NEW hook for this topic using the SAME patterns but different words:
Topic: {topic}
Category: {category}

Keep the same structure and psychological triggers.
Return ONLY the new hook (7-10 words max), no explanation."""
                
                result = self._call_gemini(prompt)
                if result and len(result.split()) <= 12:
                    safe_print(f"   [HOOK] Applied learned pattern!")
                    return self._clean_hook(result)
        except:
            pass
        
        return None
    
    def _generate_with_ai(self, topic: str, category: str, 
                         style: str) -> Optional[str]:
        """Generate hook using AI with HIGH-QUALITY model for best results."""
        
        # v17.9.15: Get learned patterns for enhanced prompting
        best_patterns = self.data.get("best_patterns", [])
        worst_patterns = self.data.get("worst_patterns", [])
        
        patterns_context = ""
        if best_patterns:
            patterns_context = f"\n\nPATTERNS THAT WORK (from analytics): {', '.join(best_patterns[:5])}"
        if worst_patterns:
            patterns_context += f"\nPATTERNS TO AVOID: {', '.join(worst_patterns[:3])}"
        
        prompt = f"""You are MrBeast's hook writer. You've written 1000+ viral hooks with 10B+ views.

TASK: Create ONE hook that will score 10/10 on our virality algorithm.

Topic: {topic}
Category: {category}
{patterns_context}

===== MANDATORY SCORING REQUIREMENTS (ALL must be met!) =====
Our algorithm scores hooks on these EXACT criteria. Your hook MUST include:

1. PATTERN INTERRUPT (Required for +20 points)
   Start with one of: "STOP", "Wait", "Hold on", "Listen"
   Example: "STOP - this changes everything"

2. QUESTION OR NUMBER (Required for +15 points each)
   Include a "?" OR a specific number
   Example: "Did you know 97% of people..." or "3 things no one tells you..."

3. CURIOSITY TRIGGER (Required for +15 points)
   Include one of: "secret", "truth", "why", "how", "hidden", "actually"
   Example: "The hidden truth about..."

4. SHORT & PUNCHY (Required for +10 points)
   MAXIMUM 10 words. Less is more!

5. IDENTITY CHALLENGE (Bonus virality)
   Make them question themselves: "You're doing this wrong"

===== WINNING FORMULA =====
[PATTERN INTERRUPT] + [NUMBER/QUESTION] + [CURIOSITY WORD] + [IDENTITY HOOK]

PERFECT EXAMPLES (score 95-100):
- "STOP - the secret 3-step trick that 99% don't know"
- "Wait, why do 87% of people get this wrong?"
- "Hold on - the hidden truth about {topic} will shock you"
- "STOP scrolling - here's the real reason why..."

BAD EXAMPLES (score 20-40):
- "Here's a tip about {topic}" (no interrupt, no curiosity)
- "Let me tell you something interesting" (boring, no hook)
- "This video is about {topic}" (zero hook power)

CRITICAL: Your hook must be 10 words or less and include at least 3 of the 5 requirements above!

Return ONLY the hook text, no quotes, no explanation."""

        # Try Gemini first (more creative)
        hook = self._call_gemini(prompt)
        if hook:
            return self._clean_hook(hook)
        
        # Try Groq
        hook = self._call_groq(prompt)
        if hook:
            return self._clean_hook(hook)
        
        return None
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API with HIGH-QUALITY model for hooks."""
        if not self.gemini_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            
            # v17.9.15: Use high-quality model for hooks (critical task)
            try:
                from model_helper import get_high_quality_model
                model_name = get_high_quality_model("gemini")
            except ImportError:
                try:
                    from src.ai.model_helper import get_high_quality_model
                    model_name = get_high_quality_model("gemini")
                except:
                    model_name = None
            
            # Fall back to regular model if pro not available
            if not model_name:
                model_name = get_dynamic_gemini_model()
            
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            safe_print(f"   [!] Gemini error: {e}")
            return None
    
    def _call_groq(self, prompt: str) -> Optional[str]:
        """Call Groq API."""
        if not self.groq_key:
            return None
        try:
            from groq import Groq
            # v17.9.10: Dynamic model selection with proper fallback
            try:
                from model_helper import get_dynamic_groq_model
                model = get_dynamic_groq_model()
            except ImportError:
                try:
                    from src.ai.model_helper import get_dynamic_groq_model
                    model = get_dynamic_groq_model()
                except ImportError:
                    model = "llama-3.3-70b-versatile"  # Emergency fallback only
            
            client = Groq(api_key=self.groq_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.9  # Higher temperature for creativity
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            safe_print(f"   [!] Groq error: {e}")
            return None
    
    def _clean_hook(self, hook: str) -> str:
        """Clean and validate hook text."""
        # Remove quotes
        hook = hook.strip('"\'')
        
        # Remove newlines
        hook = hook.replace('\n', ' ').strip()
        
        # Truncate if too long (max 20 words)
        words = hook.split()
        if len(words) > 20:
            hook = ' '.join(words[:20]) + "..."
        
        return hook
    
    def _fallback_hook(self, topic: str, category: str) -> str:
        """Generate a simple fallback hook."""
        templates = [
            f"The truth about {topic} nobody talks about",
            f"Why {topic} is changing everything",
            f"STOP - you need to know this about {topic}",
            f"What they don't teach you about {topic}",
        ]
        import random
        return random.choice(templates)
    
    def generate_variations(self, base_hook: str, count: int = 3) -> List[str]:
        """
        Generate variations of a hook for A/B testing.
        """
        prompt = f"""Create {count} variations of this hook for A/B testing.
Each variation should have the same meaning but different style/wording.

Original: "{base_hook}"

Return ONLY the variations, one per line, no numbers or bullets."""

        result = self._call_gemini(prompt) or self._call_groq(prompt)
        
        if result:
            variations = [self._clean_hook(v) for v in result.strip().split('\n') if v.strip()]
            return variations[:count]
        
        return [base_hook]  # Return original if AI fails
    
    def record_performance(self, hook: str, views: int, likes: int):
        """Record hook performance for learning."""
        hook_hash = hash(hook) % 1000000  # Simple hash
        
        self.data["performance"][str(hook_hash)] = {
            "hook": hook,
            "views": views,
            "likes": likes,
            "ctr": likes / max(views, 1),
            "recorded": datetime.now().isoformat()
        }
        
        # Add to generated hooks
        if hook not in self.data["generated_hooks"]:
            self.data["generated_hooks"].append(hook)
        
        self._save()
    
    def get_best_hooks(self, count: int = 5) -> List[Dict]:
        """Get the best performing hooks."""
        if not self.data.get("performance"):
            return []
        
        sorted_hooks = sorted(
            self.data["performance"].values(),
            key=lambda x: x.get("views", 0),
            reverse=True
        )
        
        return sorted_hooks[:count]


# Singleton
_hook_generator = None


def get_hook_generator() -> AIHookGenerator:
    """Get the singleton hook generator."""
    global _hook_generator
    if _hook_generator is None:
        _hook_generator = AIHookGenerator()
    return _hook_generator


def generate_hook(topic: str, category: str) -> str:
    """Convenience function to generate a hook."""
    return get_hook_generator().generate_hook(topic, category)


if __name__ == "__main__":
    # Test
    safe_print("Testing AI Hook Generator...")
    
    gen = get_hook_generator()
    
    # Test hook generation
    topics = [
        ("Why successful people wake up at 5 AM", "productivity"),
        ("The psychology of first impressions", "psychology"),
        ("How to save $500 per month", "money"),
    ]
    
    for topic, cat in topics:
        hook = gen.generate_hook(topic, cat)
        safe_print(f"\nTopic: {topic}")
        safe_print(f"Hook: {hook}")
    
    safe_print("\nTest complete!")



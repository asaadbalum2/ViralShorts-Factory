#!/usr/bin/env python3
"""
ViralShorts Factory - AI Content Quality Checker v17.8
=======================================================

Checks content quality using AI before rendering.

Quality aspects checked:
1. Hook strength
2. Value delivery
3. Pacing
4. CTA effectiveness
5. Virality potential

This replaces hardcoded quality rules with AI judgment.
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

QUALITY_HISTORY_FILE = STATE_DIR / "quality_history.json"


class AIContentQualityChecker:
    """
    Checks content quality using AI.
    """
    
    def __init__(self):
        self.data = self._load()
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
    
    def _load(self) -> Dict:
        try:
            if QUALITY_HISTORY_FILE.exists():
                with open(QUALITY_HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "checks": [],
            "average_scores": {},
            "improvement_trends": {},
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(QUALITY_HISTORY_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def check_content(self, content: Dict) -> Dict:
        """
        Check content quality using AI.
        
        Args:
            content: Dict with hook, phrases, cta, category, topic
        
        Returns:
            Dict with score (1-10), issues, suggestions
        """
        hook = content.get("hook", "")
        phrases = content.get("phrases", [])
        cta = content.get("cta", "")
        category = content.get("category", "")
        topic = content.get("topic", "")
        
        # Try AI quality check
        ai_result = self._check_with_ai(hook, phrases, cta, category, topic)
        
        if ai_result:
            self._record_check(ai_result)
            return ai_result
        
        # Fallback: Simple heuristic check
        return self._fallback_check(hook, phrases, cta)
    
    def _check_with_ai(self, hook: str, phrases: List[str], 
                      cta: str, category: str, topic: str) -> Optional[Dict]:
        """Check quality with AI."""
        full_content = f"Hook: {hook}\n\nPhrases:\n" + "\n".join(phrases) + f"\n\nCTA: {cta}"
        
        prompt = f"""You are a viral content quality expert. Evaluate this YouTube Short script.

CONTENT:
Topic: {topic}
Category: {category}

{full_content}

EVALUATE (1-10 scale):
1. HOOK STRENGTH: Does it stop the scroll? Create curiosity?
2. VALUE DELIVERY: Does it actually teach/reveal something?
3. PACING: Is each phrase punchy and necessary?
4. CTA EFFECTIVENESS: Will it drive engagement?
5. VIRALITY POTENTIAL: Would people share/save this?

RESPONSE FORMAT (JSON):
{{
    "score": 7,
    "hook_score": 8,
    "value_score": 6,
    "pacing_score": 7,
    "cta_score": 7,
    "virality_score": 6,
    "issues": ["specific issue 1", "specific issue 2"],
    "suggestions": ["specific fix 1", "specific fix 2"],
    "verdict": "PASS" or "NEEDS_WORK"
}}

Return ONLY valid JSON."""

        result = self._call_ai(prompt)
        
        if result:
            return self._parse_result(result)
        
        return None
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """Call AI."""
        # Try Groq first (faster)
        if self.groq_key:
            try:
                from groq import Groq
                try:
                    from quota_optimizer import get_best_groq_model
                    model = get_best_groq_model(self.groq_key)
                except ImportError:
                    try:
                        from src.ai.model_helper import get_dynamic_groq_model
                        model = get_dynamic_groq_model()
                    except:
                        model = "llama-3.3-70b-versatile"  # Emergency only
                
                client = Groq(api_key=self.groq_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.3  # Low temp for consistent scoring
                )
                return response.choices[0].message.content
            except Exception as e:
                safe_print(f"   [!] Groq error: {e}")
        
        # Try Gemini
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(get_dynamic_gemini_model())
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                safe_print(f"   [!] Gemini error: {e}")
        
        return None
    
    def _parse_result(self, result: str) -> Optional[Dict]:
        """Parse AI result."""
        try:
            # Extract JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception as e:
            safe_print(f"   [!] Parse error: {e}")
        
        return None
    
    def _fallback_check(self, hook: str, phrases: List[str], cta: str) -> Dict:
        """Simple heuristic quality check."""
        score = 5  # Start at 5
        issues = []
        suggestions = []
        
        # Hook checks
        if len(hook) < 10:
            issues.append("Hook too short")
            suggestions.append("Add more words to hook for impact")
        elif len(hook) > 100:
            issues.append("Hook too long")
            suggestions.append("Shorten hook to under 15 words")
        else:
            score += 1
        
        # Hook patterns
        hook_lower = hook.lower()
        if any(w in hook_lower for w in ["stop", "wait", "did you know", "?", "secret"]):
            score += 1
        else:
            suggestions.append("Add scroll-stopping pattern (question, STOP, etc)")
        
        # Phrase count
        if 3 <= len(phrases) <= 6:
            score += 1
        elif len(phrases) < 3:
            issues.append("Not enough phrases for value")
            suggestions.append("Add more content phrases")
        
        # CTA check
        if cta:
            if "?" in cta or "comment" in cta.lower():
                score += 1
            else:
                suggestions.append("Add engagement-driving CTA")
        else:
            issues.append("Missing CTA")
            suggestions.append("Add a call-to-action at the end")
        
        # Cap at 10
        score = min(score, 10)
        
        return {
            "score": score,
            "hook_score": min(score + 1, 10),
            "value_score": score,
            "pacing_score": score,
            "cta_score": score if cta else 4,
            "virality_score": score,
            "issues": issues,
            "suggestions": suggestions,
            "verdict": "PASS" if score >= 7 else "NEEDS_WORK",
            "source": "heuristic_fallback"
        }
    
    def _record_check(self, result: Dict):
        """Record check result for trends."""
        self.data["checks"].append({
            "score": result.get("score"),
            "verdict": result.get("verdict"),
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 checks
        self.data["checks"] = self.data["checks"][-100:]
        
        # Update averages
        recent = self.data["checks"][-20:]
        if recent:
            self.data["average_scores"]["last_20"] = sum(c.get("score", 0) for c in recent) / len(recent)
        
        self._save()
    
    def get_quality_trends(self) -> Dict:
        """Get quality trends over time."""
        checks = self.data.get("checks", [])
        
        if not checks:
            return {"trend": "no_data", "average": 0}
        
        recent = checks[-10:]
        older = checks[-20:-10] if len(checks) >= 20 else []
        
        recent_avg = sum(c.get("score", 0) for c in recent) / len(recent) if recent else 0
        older_avg = sum(c.get("score", 0) for c in older) / len(older) if older else recent_avg
        
        if recent_avg > older_avg + 0.5:
            trend = "improving"
        elif recent_avg < older_avg - 0.5:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "average": recent_avg,
            "change": recent_avg - older_avg
        }


# Singleton
_quality_checker = None


def get_quality_checker() -> AIContentQualityChecker:
    """Get singleton quality checker."""
    global _quality_checker
    if _quality_checker is None:
        _quality_checker = AIContentQualityChecker()
    return _quality_checker


def check_content_quality(content: Dict) -> Dict:
    """Convenience function to check content quality."""
    return get_quality_checker().check_content(content)


if __name__ == "__main__":
    # Test
    safe_print("Testing AI Content Quality Checker...")
    
    checker = get_quality_checker()
    
    # Test content
    test_content = {
        "hook": "STOP - This simple habit changed my life",
        "phrases": [
            "Wake up 30 minutes earlier every day",
            "Use that time for deep work",
            "You'll get 3x more done before noon",
            "I've done this for 6 months and doubled my income"
        ],
        "cta": "Comment: What time do you wake up?",
        "category": "productivity",
        "topic": "Morning routines for success"
    }
    
    result = checker.check_content(test_content)
    
    safe_print(f"\nQuality Check Result:")
    safe_print(f"  Score: {result.get('score')}/10")
    safe_print(f"  Verdict: {result.get('verdict')}")
    safe_print(f"  Issues: {result.get('issues', [])}")
    safe_print(f"  Suggestions: {result.get('suggestions', [])}")
    
    safe_print("\nTest complete!")



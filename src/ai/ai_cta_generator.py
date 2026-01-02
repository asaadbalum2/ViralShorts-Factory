#!/usr/bin/env python3
"""
ViralShorts Factory - AI CTA Generator v17.8
=============================================

Generates call-to-action endings using AI.

CTAs are crucial for:
- Driving engagement (likes, comments, shares)
- Building subscribers
- Creating community

This module:
1. Generates CTAs based on content type
2. Learns which CTAs perform best
3. A/B tests different CTA styles
"""

import os
import json
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def safe_print(msg: str):
    """Print with Unicode fallback."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(re.sub(r'[^\x00-\x7F]+', '', msg))


STATE_DIR = Path("./data/persistent")
STATE_DIR.mkdir(parents=True, exist_ok=True)

CTA_PERFORMANCE_FILE = STATE_DIR / "cta_performance.json"


class AICTAGenerator:
    """
    Generates viral CTAs using AI and learns from performance.
    """
    
    def __init__(self):
        self.data = self._load()
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
    
    def _load(self) -> Dict:
        try:
            if CTA_PERFORMANCE_FILE.exists():
                with open(CTA_PERFORMANCE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "generated_ctas": [],
            "performance": {},
            "best_styles": [],
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(CTA_PERFORMANCE_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def generate_cta(self, topic: str, category: str,
                    style: str = "auto") -> str:
        """
        Generate a scroll-stopping CTA.
        
        Args:
            topic: Video topic
            category: Content category
            style: CTA style (comment, subscribe, save, share, auto)
        
        Returns:
            The CTA text
        """
        # First try: Get best-performing learned CTA
        learned = self._try_learned_cta(category)
        if learned:
            safe_print(f"   [CTA] Using learned CTA")
            return learned
        
        # Second try: Generate with AI
        ai_cta = self._generate_with_ai(topic, category, style)
        if ai_cta:
            safe_print(f"   [CTA] AI-generated CTA")
            return ai_cta
        
        # Fallback: Simple template
        return self._fallback_cta(category, style)
    
    def _try_learned_cta(self, category: str) -> Optional[str]:
        """Try to use a learned best-performing CTA."""
        if not self.data.get("performance"):
            return None
        
        # Find best CTAs for this category
        best_cta = None
        best_score = 0
        
        for key, stats in self.data["performance"].items():
            if stats.get("category") == category:
                score = stats.get("comments", 0) + stats.get("engagement", 0)
                if score > best_score:
                    best_score = score
                    best_cta = stats.get("cta")
        
        return best_cta if best_score > 10 else None  # Only use if proven
    
    def _generate_with_ai(self, topic: str, category: str,
                         style: str) -> Optional[str]:
        """Generate CTA with AI."""
        style_hint = ""
        if style == "comment":
            style_hint = "Focus on driving comments - ask a question that DEMANDS a response."
        elif style == "subscribe":
            style_hint = "Focus on subscribing - create urgency around not missing future content."
        elif style == "save":
            style_hint = "Focus on saving - emphasize the reference value of this content."
        elif style == "share":
            style_hint = "Focus on sharing - appeal to helping friends/family."
        else:
            style_hint = "Choose the best style for maximum engagement."
        
        prompt = f"""You are a viral content strategist who creates CTAs that drive engagement.

TASK: Create ONE powerful CTA (call-to-action) for the end of this video.

Topic: {topic}
Category: {category}
Style: {style_hint}

CTA REQUIREMENTS:
1. Must be 10-20 words MAX
2. Must feel natural (not pushy)
3. Must create urgency or curiosity
4. Must be specific to the content
5. Should drive comments, likes, or subscribes

EFFECTIVE CTA PATTERNS:
- Question: "Comment below: What's YOUR biggest challenge with this?"
- Challenge: "Save this and try it for 7 days - you'll thank me later"
- Poll: "Type 1 if you knew this, 2 if you didn't"
- Curiosity: "Follow for Part 2 where I reveal the secret weapon"
- Social proof: "Join 10,000 others who already tried this"

Return ONLY the CTA text, no quotes, no explanation."""

        result = self._call_ai(prompt)
        if result:
            return self._clean_cta(result)
        
        return None
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """Call AI."""
        # Try Gemini
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                safe_print(f"   [!] Gemini error: {e}")
        
        # Try Groq
        if self.groq_key:
            try:
                from groq import Groq
                try:
                    from quota_optimizer import get_best_groq_model
                    model = get_best_groq_model(self.groq_key)
                except ImportError:
                    model = "llama-3.3-70b-versatile"
                
                client = Groq(api_key=self.groq_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0.8
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                safe_print(f"   [!] Groq error: {e}")
        
        return None
    
    def _clean_cta(self, cta: str) -> str:
        """Clean CTA text."""
        cta = cta.strip('"\'')
        cta = cta.replace('\n', ' ').strip()
        
        # Truncate if too long
        words = cta.split()
        if len(words) > 25:
            cta = ' '.join(words[:25])
        
        return cta
    
    def _fallback_cta(self, category: str, style: str) -> str:
        """Generate fallback CTA."""
        templates = {
            "comment": [
                "Comment below: Did you know this?",
                "Type 1 if you agree, 2 if you disagree",
                "What's YOUR take on this? Comment!",
            ],
            "subscribe": [
                "Follow for more content like this!",
                "Don't miss Part 2 - hit that follow button!",
            ],
            "save": [
                "Save this for later - you'll need it!",
                "Bookmark this and thank me later",
            ],
            "share": [
                "Share this with someone who needs it!",
                "Tag a friend who should see this",
            ],
        }
        
        if style in templates:
            return random.choice(templates[style])
        
        # Default: comment-focused
        return random.choice(templates["comment"])
    
    def record_performance(self, cta: str, category: str,
                          comments: int, likes: int, shares: int = 0):
        """Record CTA performance for learning."""
        key = f"{hash(cta) % 10000}"
        
        self.data["performance"][key] = {
            "cta": cta,
            "category": category,
            "comments": comments,
            "likes": likes,
            "shares": shares,
            "engagement": comments + likes + (shares * 2),
            "recorded": datetime.now().isoformat()
        }
        
        self._save()
    
    def get_best_ctas(self, count: int = 5) -> List[Dict]:
        """Get best performing CTAs."""
        if not self.data.get("performance"):
            return []
        
        sorted_ctas = sorted(
            self.data["performance"].values(),
            key=lambda x: x.get("engagement", 0),
            reverse=True
        )
        
        return sorted_ctas[:count]


# Singleton
_cta_generator = None


def get_cta_generator() -> AICTAGenerator:
    """Get singleton CTA generator."""
    global _cta_generator
    if _cta_generator is None:
        _cta_generator = AICTAGenerator()
    return _cta_generator


def generate_cta(topic: str, category: str) -> str:
    """Convenience function to generate CTA."""
    return get_cta_generator().generate_cta(topic, category)


if __name__ == "__main__":
    # Test
    safe_print("Testing AI CTA Generator...")
    
    gen = get_cta_generator()
    
    # Test CTA generation
    tests = [
        ("Why successful people wake up at 5 AM", "productivity"),
        ("Money mistakes in your 20s", "money"),
        ("Signs of high intelligence", "psychology"),
    ]
    
    for topic, cat in tests:
        cta = gen.generate_cta(topic, cat)
        safe_print(f"\nTopic: {topic}")
        safe_print(f"CTA: {cta}")
    
    safe_print("\nTest complete!")


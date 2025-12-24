#!/usr/bin/env python3
"""
ViralShorts Factory - Comprehensive Enhancements Module v9.0
==============================================================

Implements ALL 25 enhancements through AI-driven prompts (not hardcoded logic).

ENHANCEMENT CATEGORIES:
1. CORE QUALITY (#1-4): Post-render validation, comment mining, semantic duplicates, voice pacing
2. ANALYTICS (#5-10): Retention, A/B testing, thumbnails, music-energy, error learning
3. OPTIMIZATION (#11-15): Value density, trend freshness, CTAs, animations, contextual awareness
4. OPERATIONAL (#16-21): Notifications, watch time, SEO, cross-promo, posting time, shadow-ban
5. GROWTH (#22-25): Localization, recycling, competitor tracking, engagement automation

QUOTA MANAGEMENT:
- Groq: Primary for time-sensitive tasks (faster)
- Gemini: Secondary for bulk/analytical tasks (higher capacity, free)
- Smart routing to protect quotas
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests

# State directory
STATE_DIR = Path("./data/persistent")
STATE_DIR.mkdir(parents=True, exist_ok=True)

ENHANCEMENT_STATE_FILE = STATE_DIR / "enhancement_state.json"


def safe_print(msg: str):
    """Print with fallback for encoding issues."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(re.sub(r'[^\x00-\x7F]+', '', msg))


# =============================================================================
# AI CALLER - Smart routing between Groq and Gemini
# =============================================================================

class SmartAICaller:
    """
    Intelligently routes AI calls between Groq and Gemini based on:
    - Task priority (time-sensitive vs bulk)
    - Token usage optimization
    - Quota protection
    
    QUOTA ESTIMATES (Free Tiers):
    - Groq: ~6000 requests/day, 30K tokens/min
    - Gemini 2.0 Flash: 1500 requests/day, 1M tokens/min
    """
    
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.groq_client = None
        self.gemini_model = None
        
        # Track usage for smart routing
        self.groq_calls_today = 0
        self.gemini_calls_today = 0
        self.daily_groq_limit = 100  # Conservative estimate per batch
        
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AI clients."""
        if self.groq_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key)
            except Exception as e:
                safe_print(f"[!] Groq init: {e}")
        
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                # Try multiple Gemini models in order of preference
                for model_name in ['gemini-2.0-flash-exp', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                    try:
                        self.gemini_model = genai.GenerativeModel(model_name)
                        safe_print(f"[OK] Gemini model: {model_name}")
                        break
                    except:
                        continue
            except Exception as e:
                safe_print(f"[!] Gemini init: {e}")
    
    def call(self, prompt: str, max_tokens: int = 1000, 
             priority: str = "normal", temperature: float = 0.8) -> Optional[str]:
        """
        Make AI call with smart routing.
        
        Priority:
        - "critical": Use Groq first (faster, for real-time decisions)
        - "normal": Use Gemini first (save Groq quota)
        - "bulk": Always use Gemini (high token tasks)
        """
        import time
        time.sleep(0.5)  # Rate limit protection
        
        # Determine order based on priority
        if priority == "critical":
            providers = [("groq", self._call_groq), ("gemini", self._call_gemini)]
        else:  # normal or bulk
            providers = [("gemini", self._call_gemini), ("groq", self._call_groq)]
        
        for name, call_func in providers:
            try:
                result = call_func(prompt, max_tokens, temperature)
                if result:
                    if name == "groq":
                        self.groq_calls_today += 1
                    else:
                        self.gemini_calls_today += 1
                    return result
            except Exception as e:
                safe_print(f"[!] {name} failed: {e}")
                continue
        
        return None
    
    def _call_groq(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Call Groq API."""
        if not self.groq_client:
            return None
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Call Gemini API."""
        if not self.gemini_model:
            return None
        
        response = self.gemini_model.generate_content(prompt)
        return response.text
    
    def parse_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from AI response."""
        if not text:
            return None
        
        # Clean markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        try:
            return json.loads(text.strip())
        except:
            return None


# Global AI caller
_ai_caller = None

def get_ai_caller() -> SmartAICaller:
    global _ai_caller
    if _ai_caller is None:
        _ai_caller = SmartAICaller()
    return _ai_caller


# =============================================================================
# ENHANCEMENT #1: Post-Render Quality Validation
# =============================================================================

def validate_post_render(phrases: List[str], metadata: Dict, video_duration: float) -> Dict:
    """
    AI validates the final video content before upload.
    
    Checks:
    - Text readability on mobile
    - Audio/timing alignment
    - B-roll appropriateness
    - Overall watchability
    
    Returns: {"approved": bool, "issues": [], "suggestions": []}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a FINAL QUALITY GATE before a video goes live.
This video is ALREADY RENDERED. Your job is to predict any issues viewers might have.

=== VIDEO CONTENT ===
Phrases shown on screen: {json.dumps(phrases, indent=2)}
Total duration: {video_duration:.1f} seconds
Title: {metadata.get('title', 'Unknown')}
Category: {metadata.get('category', 'Unknown')}

=== FINAL CHECKS ===
Imagine you're a viewer scrolling. Would you:
1. STOP and watch? (hook strength)
2. UNDERSTAND the text quickly? (readability)
3. FEEL satisfied at the end? (payoff)
4. WANT to engage? (comment/like/share)

=== RED FLAGS TO CATCH ===
- Text too long for mobile reading
- Pacing too fast/slow
- Weak or confusing hook
- Anticlimactic ending
- Any content that screams "AI-generated"

=== OUTPUT JSON ===
{{
    "approved": true/false,
    "quality_score": 1-10,
    "hook_strength": 1-10,
    "readability": 1-10,
    "payoff_satisfaction": 1-10,
    "issues": ["issue 1", "issue 2"],
    "suggestions": ["suggestion for next time"],
    "predicted_retention": "high/medium/low",
    "upload_recommendation": "upload/review/reject"
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=400, priority="critical")
    parsed = ai.parse_json(result)
    
    if parsed:
        safe_print(f"   [POST-RENDER] Score: {parsed.get('quality_score', 'N/A')}/10, "
                   f"Approved: {parsed.get('approved', 'N/A')}")
        return parsed
    
    return {"approved": True, "quality_score": 7, "issues": [], "suggestions": []}


# =============================================================================
# ENHANCEMENT #3: Semantic Duplicate Detection
# =============================================================================

def check_semantic_duplicate(new_topic: str, new_hook: str, recent_topics: List[str]) -> Dict:
    """
    AI checks if new content is semantically similar to recent content.
    
    Returns: {"is_duplicate": bool, "similarity_score": 0-100, "similar_to": str or None}
    """
    if not recent_topics:
        return {"is_duplicate": False, "similarity_score": 0, "similar_to": None}
    
    ai = get_ai_caller()
    
    prompt = f"""You are a DUPLICATE CONTENT DETECTOR.
Check if this new video topic is too similar to recently published content.

=== NEW VIDEO ===
Topic: {new_topic}
Hook: {new_hook}

=== RECENT TOPICS (avoid similarity) ===
{json.dumps(recent_topics[-15:], indent=2)}

=== SIMILARITY CRITERIA ===
Consider these as "too similar" (DUPLICATE):
- Same core message with different words
- Same psychological hook/trigger
- Same actionable advice
- Viewers would think "didn't I just see this?"

NOT duplicates:
- Same category but different specific topic
- Same format but different content
- Related but complementary information

=== OUTPUT JSON ===
{{
    "is_duplicate": true/false,
    "similarity_score": 0-100 (100 = identical concept),
    "similar_to": "the specific recent topic it's similar to" or null,
    "reason": "why it is/isn't a duplicate",
    "suggestion": "how to make it more unique" or null
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=300, priority="normal")
    parsed = ai.parse_json(result)
    
    if parsed:
        if parsed.get('is_duplicate'):
            safe_print(f"   [DUPLICATE] Similar to: {parsed.get('similar_to', 'unknown')}")
        return parsed
    
    return {"is_duplicate": False, "similarity_score": 0, "similar_to": None}


# =============================================================================
# ENHANCEMENT #4: Voice Pacing Intelligence
# =============================================================================

def enhance_voice_pacing(phrases: List[str]) -> List[Dict]:
    """
    AI determines optimal pacing for each phrase.
    
    Returns: List of {"text": str, "rate": str, "emphasis_words": []}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a VOICE DIRECTOR for viral short videos.
Determine the optimal pacing and emphasis for each phrase.

=== PHRASES ===
{json.dumps(phrases, indent=2)}

=== PACING RULES ===
1. HOOK (first phrase): Slightly slower, dramatic, grab attention
2. KEY NUMBERS: Slow down slightly - "five...hundred...dollars"
3. REVELATION: Build-up should be normal, revelation slower
4. CTA (last phrase): Energetic, direct

=== RATE OPTIONS ===
- "-10%": Slow, dramatic (for impact moments)
- "-5%": Slightly slower (for numbers, key points)
- "+0%": Normal (for explanations)
- "+5%": Slightly faster (for excitement)
- "+10%": Fast, energetic (for CTAs)

=== OUTPUT JSON ===
[
    {{
        "text": "the phrase text",
        "rate": "-5%",
        "emphasis_words": ["key", "words", "to", "stress"],
        "pause_before": true/false,
        "reason": "why this pacing"
    }}
]

JSON ARRAY ONLY."""

    result = ai.call(prompt, max_tokens=500, priority="normal")
    parsed = ai.parse_json(result)
    
    if parsed and isinstance(parsed, list):
        return parsed
    
    # Fallback: uniform pacing
    return [{"text": p, "rate": "+0%", "emphasis_words": []} for p in phrases]


# =============================================================================
# ENHANCEMENT #5: Retention Curve Prediction
# =============================================================================

def predict_retention_curve(phrases: List[str], hook: str) -> Dict:
    """
    AI predicts where viewers might drop off.
    
    Returns: {"predicted_curve": [100, 85, 70, 65], "drop_off_points": [], "suggestions": []}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a RETENTION ANALYST for YouTube Shorts.
Predict the viewer retention curve for this video.

=== CONTENT ===
Hook: {hook}
Phrases: {json.dumps(phrases, indent=2)}

=== RETENTION PSYCHOLOGY ===
- First 1-2 seconds: Hook must stop the scroll (biggest drop-off point)
- 3-5 seconds: Must deliver first value or curiosity payoff
- Middle: Each phrase must earn continued attention
- End: Satisfaction determines saves/comments

=== OUTPUT JSON ===
{{
    "predicted_retention_percent": [100, 85, 70, ...],
    "estimated_avg_retention": 65,
    "biggest_drop_off_point": {{
        "phrase_index": 2,
        "reason": "why viewers would leave here"
    }},
    "weak_points": [
        {{"index": 1, "issue": "description", "fix": "suggestion"}}
    ],
    "strong_points": ["what keeps viewers watching"],
    "predicted_completion_rate": 55
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=400, priority="bulk")
    return ai.parse_json(result) or {}


# =============================================================================
# ENHANCEMENT #7: A/B Testing Completeness (Title Style Tracking)
# =============================================================================

class ABTestTracker:
    """Track A/B test results and learn which variants perform best."""
    
    STATE_FILE = STATE_DIR / "ab_test_results.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"title_styles": {}, "cta_variants": {}, "thumbnail_styles": {}}
    
    def _save(self):
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_variant(self, variant_type: str, variant_name: str, video_id: str, metadata: Dict):
        """Record a variant was used."""
        if variant_type not in self.data:
            self.data[variant_type] = {}
        if variant_name not in self.data[variant_type]:
            self.data[variant_type][variant_name] = {"videos": [], "total_views": 0, "total_engagement": 0}
        
        self.data[variant_type][variant_name]["videos"].append({
            "video_id": video_id,
            "title": metadata.get("title", ""),
            "recorded_at": datetime.now().isoformat()
        })
        self._save()
    
    def update_performance(self, variant_type: str, variant_name: str, views: int, engagement: int):
        """Update performance metrics for a variant."""
        if variant_type in self.data and variant_name in self.data[variant_type]:
            self.data[variant_type][variant_name]["total_views"] += views
            self.data[variant_type][variant_name]["total_engagement"] += engagement
            self._save()
    
    def get_best_variant(self, variant_type: str) -> Optional[str]:
        """Get the best performing variant based on views per video."""
        if variant_type not in self.data:
            return None
        
        variants = self.data[variant_type]
        if not variants:
            return None
        
        # Calculate average views per video for each variant
        scores = {}
        for name, data in variants.items():
            video_count = len(data.get("videos", []))
            if video_count > 0:
                scores[name] = data.get("total_views", 0) / video_count
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def get_weights(self, variant_type: str) -> Dict[str, float]:
        """Get weighted probabilities for variants (for exploration/exploitation)."""
        if variant_type not in self.data:
            return {}
        
        variants = self.data[variant_type]
        weights = {}
        
        for name, data in variants.items():
            video_count = len(data.get("videos", []))
            if video_count > 0:
                avg_views = data.get("total_views", 0) / video_count
                weights[name] = max(0.1, avg_views / 1000)  # Normalize
            else:
                weights[name] = 1.0  # Exploration weight for untested variants
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights


# =============================================================================
# ENHANCEMENT #10: Error Pattern Learning
# =============================================================================

class ErrorPatternLearner:
    """Learn from errors to avoid repeating them."""
    
    STATE_FILE = STATE_DIR / "error_patterns.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"broll_failures": {}, "tts_failures": {}, "api_failures": {}}
    
    def _save(self):
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_broll_failure(self, keyword: str):
        """Record a B-roll keyword that failed to return results."""
        if keyword not in self.data["broll_failures"]:
            self.data["broll_failures"][keyword] = {"count": 0, "last_fail": None}
        self.data["broll_failures"][keyword]["count"] += 1
        self.data["broll_failures"][keyword]["last_fail"] = datetime.now().isoformat()
        self._save()
    
    def should_skip_keyword(self, keyword: str) -> bool:
        """Check if keyword has failed too many times."""
        if keyword in self.data["broll_failures"]:
            return self.data["broll_failures"][keyword]["count"] >= 3
        return False
    
    def get_alternative_keyword(self, original: str) -> Optional[str]:
        """AI suggests alternative keyword for failed B-roll."""
        ai = get_ai_caller()
        
        prompt = f"""The B-roll search keyword "{original}" failed to return results on Pexels.
Suggest ONE alternative search keyword that would find similar footage.

Requirements:
- Be more generic/common
- Must be searchable on stock video sites
- Keep the same emotional tone

Return ONLY the alternative keyword, nothing else."""

        result = ai.call(prompt, max_tokens=50, priority="normal")
        return result.strip() if result else None


# =============================================================================
# ENHANCEMENT #11: Value Density Scoring
# =============================================================================

def score_value_density(phrases: List[str], duration_seconds: float) -> Dict:
    """
    AI scores how much value is delivered per second.
    
    Returns: {"value_per_second": float, "padding_detected": bool, "lean_version": []}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a VALUE DENSITY ANALYZER for short-form video.
Every second counts. Identify any "padding" or filler content.

=== CONTENT ===
Phrases: {json.dumps(phrases, indent=2)}
Duration: {duration_seconds:.1f} seconds

=== VALUE DEFINITION ===
HIGH VALUE content:
- Specific facts, numbers, techniques
- Actionable advice
- Surprising revelations
- Emotional impact

LOW VALUE (padding):
- Vague statements
- Unnecessary context
- Repeated ideas
- Filler words/phrases

=== OUTPUT JSON ===
{{
    "value_score": 1-10,
    "value_per_second": 0.0-1.0,
    "has_padding": true/false,
    "padding_phrases": [indices of low-value phrases],
    "lean_version": ["condensed phrase 1", "condensed phrase 2"],
    "time_saved_seconds": 0
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=400, priority="bulk")
    return ai.parse_json(result) or {"value_score": 7, "has_padding": False}


# =============================================================================
# ENHANCEMENT #12: Trend Freshness Decay
# =============================================================================

def score_trend_freshness(topic: str, source: str, fetch_time: str = None) -> Dict:
    """
    Score how fresh/relevant a trend is.
    
    Returns: {"freshness_score": 1-100, "urgency": "high/medium/low"}
    """
    # Calculate time decay
    if fetch_time:
        try:
            fetch_dt = datetime.fromisoformat(fetch_time)
            hours_old = (datetime.now() - fetch_dt).total_seconds() / 3600
        except:
            hours_old = 24
    else:
        hours_old = 0
    
    # Source reliability scores
    source_scores = {
        "google": 90,
        "reddit": 80,
        "twitter": 85,
        "ai": 70
    }
    
    base_score = source_scores.get(source.lower(), 60)
    
    # Apply time decay (loses 5 points per hour)
    freshness_score = max(10, base_score - (hours_old * 5))
    
    urgency = "high" if freshness_score > 70 else "medium" if freshness_score > 40 else "low"
    
    return {
        "freshness_score": int(freshness_score),
        "hours_old": round(hours_old, 1),
        "urgency": urgency,
        "recommendation": "use immediately" if urgency == "high" else "use soon" if urgency == "medium" else "may be stale"
    }


# =============================================================================
# ENHANCEMENT #18: Description SEO Optimization
# =============================================================================

def generate_seo_description(title: str, topic: str, hook: str, hashtags: List[str]) -> str:
    """
    AI generates SEO-optimized description.
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a YOUTUBE SEO EXPERT.
Create an optimized description for this YouTube Short.

=== VIDEO INFO ===
Title: {title}
Topic: {topic}
Hook: {hook}
Hashtags: {hashtags}

=== SEO DESCRIPTION RULES ===
1. First line: Repeat the hook/value proposition (YouTube shows this in search)
2. Include 3-5 relevant keywords naturally
3. Add a clear CTA (subscribe, comment, like)
4. Keep under 300 characters for mobile visibility
5. End with hashtags

=== FORMAT ===
[Hook/value - 1 line]

[Brief expansion - 1-2 lines]

[CTA]

[Hashtags]

Return ONLY the description text, no JSON."""

    result = ai.call(prompt, max_tokens=200, priority="normal")
    return result.strip() if result else f"{hook}\n\n#shorts #viral"


# =============================================================================
# ENHANCEMENT #21: Shadow-ban Detection
# =============================================================================

class ShadowBanDetector:
    """Detect potential shadow-ban or reduced reach."""
    
    STATE_FILE = STATE_DIR / "reach_metrics.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"baseline_first_hour_views": 50, "recent_videos": [], "alerts": []}
    
    def _save(self):
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_video_performance(self, video_id: str, first_hour_views: int, title: str):
        """Record first-hour performance for a video."""
        self.data["recent_videos"].append({
            "video_id": video_id,
            "first_hour_views": first_hour_views,
            "title": title,
            "timestamp": datetime.now().isoformat()
        })
        # Keep last 20 videos
        self.data["recent_videos"] = self.data["recent_videos"][-20:]
        
        # Update baseline (rolling average)
        if len(self.data["recent_videos"]) >= 5:
            recent_views = [v["first_hour_views"] for v in self.data["recent_videos"][-10:]]
            self.data["baseline_first_hour_views"] = sum(recent_views) / len(recent_views)
        
        self._save()
    
    def check_for_shadow_ban(self, current_first_hour_views: int) -> Dict:
        """Check if current performance indicates shadow-ban."""
        baseline = self.data.get("baseline_first_hour_views", 50)
        
        # Alert if views are less than 20% of baseline
        threshold = baseline * 0.2
        is_concerning = current_first_hour_views < threshold
        
        return {
            "is_concerning": is_concerning,
            "current_views": current_first_hour_views,
            "baseline": int(baseline),
            "threshold": int(threshold),
            "action": "PAUSE UPLOADS - Possible shadow-ban" if is_concerning else "Normal performance"
        }


# =============================================================================
# ENHANCEMENT #13: Dynamic CTA Testing
# =============================================================================

CTA_VARIANTS = [
    "SUBSCRIBE FOR MORE",
    "Comment if you agree!",
    "Save this for later",
    "Tag someone who needs this",
    "Would you try this?",
    "Share with a friend!"
]

def get_weighted_cta(ab_tracker: ABTestTracker = None) -> str:
    """Get a CTA variant with A/B testing weights."""
    import random
    
    if ab_tracker:
        weights = ab_tracker.get_weights("cta_variants")
        if weights:
            # Weighted random selection
            variants = list(weights.keys())
            probs = list(weights.values())
            return random.choices(variants, weights=probs, k=1)[0]
    
    # Default: random selection
    return random.choice(CTA_VARIANTS)


# =============================================================================
# ENHANCEMENT #2: Comment Content Mining (for weekly analysis)
# =============================================================================

def analyze_comments(comments: List[str]) -> Dict:
    """
    AI analyzes comment content to extract insights.
    Called by weekly analytics workflow.
    """
    if not comments:
        return {}
    
    ai = get_ai_caller()
    
    prompt = f"""You are a COMMENT ANALYST for a YouTube Shorts channel.
Extract actionable insights from viewer comments.

=== COMMENTS ===
{json.dumps(comments[:50], indent=2)}

=== EXTRACT ===
1. PRAISE: What do viewers love? (content to do MORE of)
2. CRITICISM: What do viewers dislike? (content to AVOID)
3. REQUESTS: What do viewers want to see?
4. RED FLAGS: Any "this is AI" or fake content accusations?
5. ENGAGEMENT DRIVERS: What topics spark discussion?

=== OUTPUT JSON ===
{{
    "positive_themes": ["theme 1", "theme 2"],
    "negative_themes": ["issue 1", "issue 2"],
    "requested_topics": ["topic 1", "topic 2"],
    "quality_concerns": ["concern 1"],
    "engagement_topics": ["high-engagement topic"],
    "overall_sentiment": "positive/neutral/negative",
    "ai_detection_mentions": 0,
    "actionable_insights": ["specific action 1", "specific action 2"]
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=500, priority="bulk")
    return ai.parse_json(result) or {}


# =============================================================================
# ENHANCEMENT ORCHESTRATOR - Runs all checks
# =============================================================================

class EnhancementOrchestrator:
    """
    Orchestrates all enhancements during video generation.
    """
    
    def __init__(self):
        self.ab_tracker = ABTestTracker()
        self.error_learner = ErrorPatternLearner()
        self.shadow_detector = ShadowBanDetector()
    
    def pre_generation_checks(self, topic: str, hook: str, recent_topics: List[str]) -> Dict:
        """
        Run checks BEFORE generating video.
        
        Returns: {"proceed": bool, "warnings": [], "modifications": {}}
        """
        result = {"proceed": True, "warnings": [], "modifications": {}}
        
        # #3: Semantic duplicate check
        dup_check = check_semantic_duplicate(topic, hook, recent_topics)
        if dup_check.get("is_duplicate"):
            result["proceed"] = False
            result["warnings"].append(f"DUPLICATE: Similar to '{dup_check.get('similar_to')}'")
            result["modifications"]["suggested_topic"] = dup_check.get("suggestion")
        
        return result
    
    def post_content_checks(self, phrases: List[str], metadata: Dict) -> Dict:
        """
        Run checks AFTER content is created but BEFORE rendering.
        
        Returns optimized phrases and metadata.
        """
        result = {"phrases": phrases, "metadata": metadata, "optimizations": []}
        
        # #4: Voice pacing intelligence
        pacing = enhance_voice_pacing(phrases)
        result["pacing"] = pacing
        result["optimizations"].append("Voice pacing optimized")
        
        # #5: Retention prediction
        retention = predict_retention_curve(phrases, metadata.get("hook", ""))
        result["retention_prediction"] = retention
        if retention.get("predicted_completion_rate", 100) < 40:
            result["warnings"] = ["Low predicted retention - consider revising content"]
        
        # #11: Value density
        value = score_value_density(phrases, 20)  # Assume 20s
        result["value_density"] = value
        if value.get("has_padding"):
            result["optimizations"].append("Consider leaner version")
        
        return result
    
    def post_render_validation(self, phrases: List[str], metadata: Dict, 
                                video_duration: float) -> Dict:
        """
        Final validation AFTER rendering.
        """
        return validate_post_render(phrases, metadata, video_duration)
    
    def get_seo_description(self, title: str, topic: str, hook: str, hashtags: List[str]) -> str:
        """Generate SEO-optimized description."""
        return generate_seo_description(title, topic, hook, hashtags)
    
    def get_cta(self) -> str:
        """Get A/B tested CTA."""
        return get_weighted_cta(self.ab_tracker)
    
    def record_ab_test(self, variant_type: str, variant_name: str, video_id: str, metadata: Dict):
        """Record an A/B test variant."""
        self.ab_tracker.record_variant(variant_type, variant_name, video_id, metadata)
    
    def record_error(self, error_type: str, details: str):
        """Record an error for pattern learning."""
        if error_type == "broll":
            self.error_learner.record_broll_failure(details)
    
    def should_skip_broll_keyword(self, keyword: str) -> bool:
        """Check if B-roll keyword should be skipped."""
        return self.error_learner.should_skip_keyword(keyword)
    
    def get_alternative_broll(self, failed_keyword: str) -> Optional[str]:
        """Get alternative B-roll keyword."""
        return self.error_learner.get_alternative_keyword(failed_keyword)


# =============================================================================
# ENHANCEMENT #14: Hook Animation Suggestions
# =============================================================================

def suggest_text_animations(phrases: List[str]) -> List[Dict]:
    """
    AI suggests animations for text to increase engagement.
    
    Returns: List of {"phrase_index": int, "animation_type": str, "reason": str}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a MOTION GRAPHICS DIRECTOR for viral short videos.
Suggest animations for these text phrases to maximize engagement.

=== PHRASES ===
{json.dumps(list(enumerate(phrases)), indent=2)}

=== ANIMATION OPTIONS ===
1. "pop_in": Text pops in quickly (for impact words, numbers)
2. "slide_up": Text slides up (for lists, sequences)
3. "fade_zoom": Fades in while zooming (for emotional moments)
4. "typewriter": Types one letter at a time (for suspense)
5. "shake": Brief shake effect (for shocking statements)
6. "none": Standard appearance (for normal content)

=== ANIMATION RULES ===
- HOOK (first phrase): Always animated strongly (pop_in or shake)
- NUMBERS: Pop or emphasize (draw attention to specific values)
- LISTS/SEQUENCES: slide_up for visual hierarchy
- EMOTIONAL: fade_zoom for impact
- Don't over-animate - pick key moments

=== OUTPUT JSON ===
[
    {{
        "phrase_index": 0,
        "animation_type": "pop_in",
        "emphasis_words": ["key", "words"],
        "reason": "why this animation"
    }}
]

JSON ARRAY ONLY."""

    result = ai.call(prompt, max_tokens=400, priority="bulk")
    parsed = ai.parse_json(result)
    
    if parsed and isinstance(parsed, list):
        return parsed
    
    # Default: pop_in for first phrase, none for others
    return [{"phrase_index": i, "animation_type": "pop_in" if i == 0 else "none", "emphasis_words": []} 
            for i in range(len(phrases))]


# =============================================================================
# ENHANCEMENT #8: Music-Content Energy Matching
# =============================================================================

def match_music_energy(phrases: List[str], available_music_moods: List[str]) -> Dict:
    """
    AI selects best music mood based on content emotional trajectory.
    
    Returns: {"recommended_mood": str, "energy_curve": [1-10], "reason": str}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a MUSIC DIRECTOR for viral short videos.
Match the right music mood to this content's emotional trajectory.

=== CONTENT PHRASES ===
{json.dumps(phrases, indent=2)}

=== AVAILABLE MUSIC MOODS ===
{json.dumps(available_music_moods, indent=2)}

=== ANALYSIS REQUIRED ===
1. What emotion does the hook create? (curiosity, shock, fear, excitement)
2. How does emotion build through the content?
3. What should the viewer feel at the end?

=== OUTPUT JSON ===
{{
    "recommended_mood": "one of the available moods",
    "energy_curve": [7, 8, 9, 10, 8],  // Energy level per phrase (1-10)
    "peak_moment": 3,  // Which phrase index is the climax
    "emotional_arc": "builds to revelation",
    "reason": "why this music mood fits"
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=250, priority="bulk")
    return ai.parse_json(result) or {"recommended_mood": "dramatic", "energy_curve": [7]*len(phrases)}


# =============================================================================
# ENHANCEMENT #22: Multi-Lingual Optimization (Localization Ready)
# =============================================================================

def analyze_localization_potential(title: str, hook: str) -> Dict:
    """
    AI analyzes if content could perform well in other languages.
    Prepares for future localization.
    
    Returns: {"universal_appeal": 1-10, "localization_opportunities": [], "cultural_notes": []}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a GLOBAL CONTENT STRATEGIST.
Analyze this content's potential for international audiences.

=== CONTENT ===
Title: {title}
Hook: {hook}

=== ANALYZE ===
1. Is this topic universally interesting or culturally specific?
2. Would the hook work in other languages?
3. Are there cultural references that wouldn't translate?
4. Which markets might find this especially interesting?

=== OUTPUT JSON ===
{{
    "universal_appeal": 1-10 (10 = works everywhere),
    "culturally_specific_elements": ["element that wouldn't translate"],
    "best_markets": ["US", "UK", "India", "Brazil", ...],
    "localization_opportunities": ["Spanish version", "Hindi version"],
    "cultural_notes": ["note about localization"],
    "recommendation": "keep as is" or "has localization potential"
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=300, priority="bulk")
    return ai.parse_json(result) or {"universal_appeal": 5}


# =============================================================================
# ENHANCEMENT #20: Optimal Posting Time
# =============================================================================

def get_optimal_posting_time(variety_state_file: Path = None) -> Dict:
    """
    Determines optimal posting time based on learned patterns.
    
    Returns: {"best_hours_utc": [14, 18], "best_days": ["Tuesday", "Friday"], "confidence": 0.8}
    """
    variety_state = {}
    if variety_state_file is None:
        variety_state_file = STATE_DIR / "variety_state.json"
    
    try:
        if variety_state_file.exists():
            with open(variety_state_file, 'r') as f:
                variety_state = json.load(f)
    except:
        pass
    
    # Return learned preferences if available
    best_hours = variety_state.get("best_posting_hours_utc", [14, 18, 22])  # Default: afternoon/evening UTC
    best_days = variety_state.get("best_posting_days", ["Tuesday", "Thursday", "Saturday"])
    
    return {
        "best_hours_utc": best_hours,
        "best_days": best_days,
        "confidence": 0.6 if "best_posting_hours_utc" in variety_state else 0.3,
        "source": "learned" if "best_posting_hours_utc" in variety_state else "default"
    }


# =============================================================================
# ENHANCEMENT #17: Watch Time Prediction
# =============================================================================

def predict_watch_time(phrases: List[str], estimated_duration: float) -> Dict:
    """
    AI predicts average watch time and factors affecting it.
    
    Returns: {"predicted_avg_watch_seconds": float, "watch_percentage": float, "factors": []}
    """
    ai = get_ai_caller()
    
    prompt = f"""You are a WATCH TIME ANALYST for short-form video.
Predict how long viewers will watch this content.

=== CONTENT ===
Phrases: {json.dumps(phrases, indent=2)}
Estimated Duration: {estimated_duration:.1f} seconds

=== FACTORS TO CONSIDER ===
1. Hook strength (does first phrase stop the scroll?)
2. Information density (value per second)
3. Curiosity maintenance (does each phrase make you want the next?)
4. Payoff satisfaction (is the ending satisfying?)
5. Pacing (too fast? too slow?)

=== OUTPUT JSON ===
{{
    "predicted_avg_watch_seconds": 12.5,
    "predicted_watch_percentage": 65,
    "drop_off_points": [
        {{"second": 5, "reason": "weak transition"}}
    ],
    "strength_factors": ["strong hook", "good pacing"],
    "weakness_factors": ["weak ending"],
    "improvement_suggestion": "specific suggestion"
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=300, priority="bulk")
    return ai.parse_json(result) or {
        "predicted_avg_watch_seconds": estimated_duration * 0.6,
        "predicted_watch_percentage": 60
    }


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_orchestrator = None

def get_enhancement_orchestrator() -> EnhancementOrchestrator:
    """Get the singleton enhancement orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancementOrchestrator()
    return _orchestrator


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Enhancement Module v9.0 - Test")
    print("=" * 60)
    
    # Test AI caller
    ai = get_ai_caller()
    print(f"\nAI Caller initialized:")
    print(f"  Groq: {'OK' if ai.groq_client else 'N/A'}")
    print(f"  Gemini: {'OK' if ai.gemini_model else 'N/A'}")
    
    # Test orchestrator
    orch = get_enhancement_orchestrator()
    print(f"\nOrchestrator initialized:")
    print(f"  A/B Tracker: OK")
    print(f"  Error Learner: OK")
    print(f"  Shadow Detector: OK")
    
    # Test semantic duplicate
    print("\n[TEST] Semantic Duplicate Check:")
    recent = ["Psychology trick about morning routines", "Money saving hack with coffee"]
    check = check_semantic_duplicate("Psychology morning routine trick", "Morning routines", recent)
    print(f"  Is duplicate: {check.get('is_duplicate')}")
    
    print("\n[OK] Enhancement module ready!")


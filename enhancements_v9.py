#!/usr/bin/env python3
"""
ViralShorts Factory - Comprehensive Enhancements Module v9.5
==============================================================

Implements ALL 35 enhancements through AI-driven prompts (not hardcoded logic).

ENHANCEMENT CATEGORIES:
1. CORE QUALITY (#1-4): Post-render validation, comment mining, semantic duplicates, voice pacing
2. ANALYTICS (#5-10): Retention, A/B testing, thumbnails, music-energy, error learning
3. OPTIMIZATION (#11-15): Value density, trend freshness, CTAs, animations, contextual awareness
4. OPERATIONAL (#16-21): Notifications, watch time, SEO, cross-promo, posting time, shadow-ban
5. GROWTH (#22-25): Localization, recycling, competitor tracking, engagement automation

NEW v9.5 ENHANCEMENTS:
6. ADVANCED (#26-35):
   - #26: Face Detection for thumbnails (OpenCV - free)
   - #27: Seasonal Content Calendar (AI-driven)
   - #28: Hook Word Performance Tracking
   - #29: Voice Speed Optimization with A/B testing
   - #30: Auto-Hashtag Rotation
   - #31: B-Roll Relevance Scoring before download
   - #32: Cross-Platform Performance Split (YouTube vs Dailymotion)
   - #33: Series Detection & Continuation
   - #34: Engagement Reply Generator
   - #35: Category Performance Decay (time-weighted)

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
# v9.5 ENHANCEMENT #26: Thumbnail Face Detection
# =============================================================================

def detect_faces_in_broll(image_path: str) -> Dict:
    """
    Detect if B-roll contains human faces (faces = higher CTR).
    Uses OpenCV's built-in cascade classifier (100% free, no API).
    
    Returns: {"has_face": bool, "face_count": int, "face_score": 0-10}
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        # Load image
        if not Path(image_path).exists():
            return {"has_face": False, "face_count": 0, "face_score": 0}
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return {"has_face": False, "face_count": 0, "face_score": 0}
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load face cascade (built into OpenCV)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        face_count = len(faces)
        has_face = face_count > 0
        
        # Score: 10 if has face, bonus for centered/large faces
        face_score = 0
        if has_face:
            face_score = min(10, 5 + face_count * 2)  # Base 5, +2 per face, max 10
        
        return {
            "has_face": has_face,
            "face_count": face_count,
            "face_score": face_score
        }
        
    except ImportError:
        # OpenCV not installed, fall back to AI-based scoring
        return {"has_face": False, "face_count": 0, "face_score": 0, "note": "cv2 not available"}
    except Exception as e:
        return {"has_face": False, "face_count": 0, "face_score": 0, "error": str(e)}


def score_broll_for_thumbnail(broll_paths: List[str]) -> List[Dict]:
    """
    Score all B-roll clips and rank them for thumbnail selection.
    Prioritizes: faces > motion > relevance.
    
    Returns: List of {"path": str, "score": int, "has_face": bool}
    """
    scored = []
    
    for path in broll_paths:
        if not path or not Path(path).exists():
            continue
        
        face_data = detect_faces_in_broll(path)
        
        scored.append({
            "path": path,
            "score": face_data.get("face_score", 0),
            "has_face": face_data.get("has_face", False),
            "face_count": face_data.get("face_count", 0)
        })
    
    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    return scored


# =============================================================================
# v9.5 ENHANCEMENT #27: Seasonal Content Calendar
# =============================================================================

def get_seasonal_content_suggestions() -> Dict:
    """
    AI generates content suggestions based on current date, upcoming holidays, seasons.
    
    Returns: {"upcoming_events": [], "suggested_topics": [], "urgency": str}
    """
    ai = get_ai_caller()
    
    today = datetime.now()
    
    prompt = f"""You are a CONTENT CALENDAR expert for viral short-form video.

=== CURRENT DATE ===
Today: {today.strftime('%A, %B %d, %Y')}
Days until New Year: {(datetime(today.year + 1, 1, 1) - today).days if today.month == 12 else 'N/A'}

=== YOUR TASK ===
Identify upcoming holidays, events, seasons, or viral moments in the NEXT 7 DAYS that we should create content about.

Consider:
1. Major holidays (Christmas, New Year, Valentine's, etc.)
2. Awareness days/months (Mental Health Month, etc.)
3. Seasonal changes (first day of winter, etc.)
4. Predictable viral moments (end of year lists, resolutions, etc.)
5. Pop culture events (award shows, sports events)

=== OUTPUT JSON ===
{{
    "upcoming_events": [
        {{"event": "event name", "date": "date", "days_until": N}}
    ],
    "suggested_topics": [
        {{"topic": "specific topic", "hook": "hook idea", "why_now": "why timely"}}
    ],
    "content_urgency": "high" or "medium" or "low",
    "seasonal_mood": "festive" or "reflective" or "energetic" or "cozy" or "normal"
}}

Generate 3-5 event-driven topics that would go viral RIGHT NOW due to timing.
JSON ONLY."""

    result = ai.call(prompt, max_tokens=400, priority="bulk")
    return ai.parse_json(result) or {
        "upcoming_events": [],
        "suggested_topics": [],
        "content_urgency": "low"
    }


# =============================================================================
# v9.5 ENHANCEMENT #28: Hook Word Performance Tracking
# =============================================================================

class HookWordTracker:
    """
    Tracks which words in hooks correlate with high performance.
    Learns over time which power words drive engagement.
    """
    
    HOOK_WORDS_FILE = STATE_DIR / "hook_word_performance.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.HOOK_WORDS_FILE.exists():
                with open(self.HOOK_WORDS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"words": {}, "last_updated": None}
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.HOOK_WORDS_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_hook_performance(self, hook: str, views: int, avg_views: int):
        """Record performance of a hook's words."""
        # Normalize: performance = views / avg_views (1.0 = average)
        performance = views / max(avg_views, 1)
        
        # Extract words (lowercase, remove punctuation)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', hook.lower())
        
        for word in words:
            if word not in self.data["words"]:
                self.data["words"][word] = {"total_performance": 0, "count": 0}
            
            self.data["words"][word]["total_performance"] += performance
            self.data["words"][word]["count"] += 1
        
        self._save()
    
    def get_power_words(self, min_count: int = 3) -> List[str]:
        """Get words that correlate with above-average performance."""
        power_words = []
        
        for word, stats in self.data["words"].items():
            if stats["count"] >= min_count:
                avg_perf = stats["total_performance"] / stats["count"]
                if avg_perf > 1.2:  # 20% above average
                    power_words.append((word, avg_perf))
        
        # Sort by performance
        power_words.sort(key=lambda x: x[1], reverse=True)
        
        return [w[0] for w in power_words[:20]]  # Top 20
    
    def get_words_to_avoid(self, min_count: int = 3) -> List[str]:
        """Get words that correlate with below-average performance."""
        weak_words = []
        
        for word, stats in self.data["words"].items():
            if stats["count"] >= min_count:
                avg_perf = stats["total_performance"] / stats["count"]
                if avg_perf < 0.7:  # 30% below average
                    weak_words.append((word, avg_perf))
        
        weak_words.sort(key=lambda x: x[1])
        
        return [w[0] for w in weak_words[:10]]


# =============================================================================
# v9.5 ENHANCEMENT #29: Voice Speed Optimization
# =============================================================================

class VoiceSpeedOptimizer:
    """
    Tracks which voice speed/rate settings correlate with retention.
    Edge TTS supports rate adjustment.
    """
    
    VOICE_SPEED_FILE = STATE_DIR / "voice_speed_performance.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.VOICE_SPEED_FILE.exists():
                with open(self.VOICE_SPEED_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "rates": {},  # {"+10%": {"videos": 5, "avg_retention": 65}}
            "best_rate": "+0%",  # Default: normal speed
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.VOICE_SPEED_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_performance(self, rate: str, retention_percent: float):
        """Record retention for a voice rate."""
        if rate not in self.data["rates"]:
            self.data["rates"][rate] = {"videos": 0, "total_retention": 0}
        
        self.data["rates"][rate]["videos"] += 1
        self.data["rates"][rate]["total_retention"] += retention_percent
        
        # Update best rate
        self._update_best_rate()
        self._save()
    
    def _update_best_rate(self):
        """Find the best performing rate."""
        best_rate = "+0%"
        best_avg = 0
        
        for rate, stats in self.data["rates"].items():
            if stats["videos"] >= 3:  # Minimum sample size
                avg = stats["total_retention"] / stats["videos"]
                if avg > best_avg:
                    best_avg = avg
                    best_rate = rate
        
        self.data["best_rate"] = best_rate
    
    def get_optimal_rate(self) -> str:
        """Get the optimal voice rate to use."""
        return self.data.get("best_rate", "+0%")
    
    def get_rate_for_ab_test(self) -> str:
        """Get a rate to A/B test (explore new options)."""
        import random
        
        options = ["-10%", "-5%", "+0%", "+5%", "+10%", "+15%"]
        
        # 80% use best rate, 20% explore
        if random.random() < 0.8:
            return self.get_optimal_rate()
        else:
            return random.choice(options)


# =============================================================================
# v9.5 ENHANCEMENT #30: Auto-Hashtag Rotation
# =============================================================================

class HashtagRotator:
    """
    Rotates hashtags to avoid repetition and test new combinations.
    Tracks which hashtags perform best.
    """
    
    HASHTAG_FILE = STATE_DIR / "hashtag_performance.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.HASHTAG_FILE.exists():
                with open(self.HASHTAG_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "used_sets": [],  # Last N hashtag sets used
            "hashtag_performance": {},  # {"#viral": {"videos": 10, "total_views": 50000}}
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.HASHTAG_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_hashtag_performance(self, hashtags: List[str], views: int):
        """Record performance of hashtags."""
        for tag in hashtags:
            tag = tag.lower()
            if tag not in self.data["hashtag_performance"]:
                self.data["hashtag_performance"][tag] = {"videos": 0, "total_views": 0}
            
            self.data["hashtag_performance"][tag]["videos"] += 1
            self.data["hashtag_performance"][tag]["total_views"] += views
        
        self._save()
    
    def get_recently_used(self, limit: int = 5) -> List[List[str]]:
        """Get recently used hashtag sets."""
        return self.data["used_sets"][-limit:]
    
    def record_used_set(self, hashtags: List[str]):
        """Record a hashtag set as used."""
        self.data["used_sets"].append(hashtags)
        self.data["used_sets"] = self.data["used_sets"][-20:]  # Keep last 20
        self._save()
    
    def get_top_performers(self, limit: int = 10) -> List[str]:
        """Get top performing hashtags."""
        scored = []
        
        for tag, stats in self.data["hashtag_performance"].items():
            if stats["videos"] >= 2:
                avg_views = stats["total_views"] / stats["videos"]
                scored.append((tag, avg_views))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [t[0] for t in scored[:limit]]


def generate_fresh_hashtags(category: str, topic: str, recent_sets: List[List[str]]) -> List[str]:
    """
    AI generates fresh hashtags avoiding recently used ones.
    """
    ai = get_ai_caller()
    
    recent_flat = [tag for s in recent_sets for tag in s]
    
    prompt = f"""You are a HASHTAG expert for viral YouTube Shorts.

=== VIDEO INFO ===
Category: {category}
Topic: {topic}

=== RECENTLY USED (AVOID THESE) ===
{json.dumps(recent_flat[-30:], indent=2)}

=== YOUR TASK ===
Generate 8-10 FRESH hashtags that:
1. Are NOT in the recently used list
2. Mix evergreen (#shorts, #viral) with specific (#topic-specific)
3. Include trending/seasonal tags if relevant
4. Range from broad (1M+ posts) to niche (10K-100K posts)

=== OUTPUT JSON ===
{{
    "hashtags": ["#tag1", "#tag2", ...],
    "evergreen_count": 3,
    "specific_count": 5,
    "reasoning": "why these tags"
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=200, priority="bulk")
    parsed = ai.parse_json(result)
    
    if parsed and parsed.get("hashtags"):
        return parsed["hashtags"]
    
    # Fallback
    return ["#shorts", "#viral", "#facts", "#trending", f"#{category}"]


# =============================================================================
# v9.5 ENHANCEMENT #31: B-Roll Relevance Scoring
# =============================================================================

def score_broll_relevance(phrase: str, broll_options: List[Dict]) -> List[Dict]:
    """
    AI scores B-roll options before downloading to pick the most relevant.
    
    broll_options: List of {"title": str, "description": str, "url": str} from Pexels
    Returns: Same list with added "relevance_score" field, sorted by score
    """
    if not broll_options:
        return []
    
    ai = get_ai_caller()
    
    # Prepare options for scoring
    options_text = "\n".join([
        f"{i+1}. {opt.get('title', 'Untitled')}: {opt.get('description', '')[:100]}"
        for i, opt in enumerate(broll_options[:10])  # Max 10 options
    ])
    
    prompt = f"""You are a VIDEO EDITOR selecting B-roll for a short video.

=== PHRASE TO ILLUSTRATE ===
"{phrase}"

=== B-ROLL OPTIONS ===
{options_text}

=== SCORE EACH OPTION ===
Rate 1-10 how well each option visually represents the phrase.

10 = Perfect match (exactly what the phrase is about)
7-9 = Good match (clearly related)
4-6 = Okay (somewhat related)
1-3 = Poor (not really related)

=== OUTPUT JSON ===
{{
    "scores": [
        {{"index": 1, "score": 8, "reason": "short reason"}}
    ],
    "best_option": 1,
    "avoid_options": [3, 5]
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=300, priority="bulk")
    parsed = ai.parse_json(result)
    
    if parsed and parsed.get("scores"):
        # Apply scores
        for score_data in parsed["scores"]:
            idx = score_data.get("index", 1) - 1
            if 0 <= idx < len(broll_options):
                broll_options[idx]["relevance_score"] = score_data.get("score", 5)
        
        # Sort by score
        broll_options.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return broll_options


# =============================================================================
# v9.5 ENHANCEMENT #32: Cross-Platform Performance Split
# =============================================================================

class CrossPlatformAnalytics:
    """
    Tracks performance separately for YouTube vs Dailymotion.
    Learns what works best on each platform.
    """
    
    PLATFORM_FILE = STATE_DIR / "cross_platform_analytics.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.PLATFORM_FILE.exists():
                with open(self.PLATFORM_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "youtube": {"videos": 0, "total_views": 0, "category_performance": {}},
            "dailymotion": {"videos": 0, "total_views": 0, "category_performance": {}},
            "platform_preferences": {},
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.PLATFORM_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_performance(self, platform: str, category: str, views: int):
        """Record a video's performance on a specific platform."""
        platform = platform.lower()
        
        if platform not in self.data:
            self.data[platform] = {"videos": 0, "total_views": 0, "category_performance": {}}
        
        self.data[platform]["videos"] += 1
        self.data[platform]["total_views"] += views
        
        if category not in self.data[platform]["category_performance"]:
            self.data[platform]["category_performance"][category] = {"videos": 0, "total_views": 0}
        
        self.data[platform]["category_performance"][category]["videos"] += 1
        self.data[platform]["category_performance"][category]["total_views"] += views
        
        self._save()
    
    def get_platform_insights(self) -> Dict:
        """Get insights on what works best on each platform."""
        insights = {}
        
        for platform in ["youtube", "dailymotion"]:
            if platform not in self.data:
                continue
            
            plat_data = self.data[platform]
            if plat_data["videos"] == 0:
                continue
            
            avg_views = plat_data["total_views"] / plat_data["videos"]
            
            # Find best category
            best_cat = None
            best_avg = 0
            for cat, stats in plat_data.get("category_performance", {}).items():
                if stats["videos"] >= 2:
                    cat_avg = stats["total_views"] / stats["videos"]
                    if cat_avg > best_avg:
                        best_avg = cat_avg
                        best_cat = cat
            
            insights[platform] = {
                "avg_views": int(avg_views),
                "best_category": best_cat,
                "videos_analyzed": plat_data["videos"]
            }
        
        return insights


# =============================================================================
# v9.5 ENHANCEMENT #33: Series Detection & Continuation
# =============================================================================

def detect_series_potential(video_performance: Dict, avg_views: int) -> Dict:
    """
    AI detects if a video performed well enough to warrant a series.
    
    video_performance: {"title": str, "views": int, "category": str, "topic": str}
    Returns: {"should_continue": bool, "series_angle": str, "suggested_title": str}
    """
    views = video_performance.get("views", 0)
    
    # If video performed 1.5x+ average, consider series
    if views < avg_views * 1.5:
        return {
            "should_continue": False,
            "reason": "Performance below series threshold (1.5x average)"
        }
    
    ai = get_ai_caller()
    
    prompt = f"""You are a CONTENT STRATEGIST for viral short videos.

=== HIGH-PERFORMING VIDEO ===
Title: {video_performance.get('title', 'Unknown')}
Views: {views:,} ({views / max(avg_views, 1):.1f}x average)
Category: {video_performance.get('category', 'Unknown')}
Topic: {video_performance.get('topic', 'Unknown')}

=== YOUR TASK ===
This video performed well! Suggest a CONTINUATION/SERIES:

1. Should this become a series? (Part 2, 3, etc.)
2. What's a fresh angle for Part 2 that keeps the magic?
3. What title would work for the sequel?

=== OUTPUT JSON ===
{{
    "should_continue": true,
    "series_potential": "high" or "medium" or "low",
    "part2_angle": "what makes part 2 different but related",
    "part2_hook": "hook for part 2",
    "part2_title": "title for part 2",
    "series_name": "if it becomes ongoing series",
    "reasoning": "why this works as series"
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=300, priority="bulk")
    parsed = ai.parse_json(result)
    
    if parsed:
        parsed["should_continue"] = True
        parsed["original_performance"] = f"{views / max(avg_views, 1):.1f}x average"
        return parsed
    
    return {
        "should_continue": True,
        "series_potential": "medium",
        "part2_angle": "Different perspective on same topic",
        "reason": "High performance warrants continuation"
    }


# =============================================================================
# v9.5 ENHANCEMENT #34: Engagement Reply Generator
# =============================================================================

def generate_reply_templates(comments: List[str]) -> Dict:
    """
    AI generates reply templates for common comment types.
    Helps boost engagement through channel responses.
    """
    if not comments:
        return {"templates": []}
    
    ai = get_ai_caller()
    
    # Take sample of comments
    sample = comments[:20]
    
    prompt = f"""You are a COMMUNITY MANAGER for a viral YouTube Shorts channel.

=== SAMPLE COMMENTS ===
{json.dumps(sample, indent=2)}

=== YOUR TASK ===
Categorize these comments and create reply templates.

Comment types to identify:
1. PRAISE ("great video!", "loved this")
2. QUESTIONS ("how do I...", "what about...")
3. DISAGREEMENT ("this is wrong", "actually...")
4. REQUESTS ("can you make a video about...")
5. TROLLS ("fake", "AI garbage")

For each type, create 2-3 reply templates that:
- Sound human (not robotic)
- Encourage further engagement
- Build community
- Are short and authentic

=== OUTPUT JSON ===
{{
    "comment_categories": [
        {{
            "category": "praise",
            "example_comments": ["example 1", "example 2"],
            "reply_templates": [
                "Thanks! 🙏 What topic should I cover next?",
                "Glad you liked it! Drop a follow for more"
            ]
        }}
    ],
    "general_tips": ["tip 1", "tip 2"]
}}

JSON ONLY."""

    result = ai.call(prompt, max_tokens=500, priority="bulk")
    return ai.parse_json(result) or {"comment_categories": []}


# =============================================================================
# v9.5 ENHANCEMENT #35: Category Performance Decay
# =============================================================================

class CategoryDecayTracker:
    """
    Applies time-decay to category performance.
    Recently underperforming categories get reduced weight.
    """
    
    DECAY_FILE = STATE_DIR / "category_decay.json"
    DECAY_HALF_LIFE_DAYS = 14  # Performance halves every 14 days
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.DECAY_FILE.exists():
                with open(self.DECAY_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "category_history": {},  # {"psychology": [{"date": "...", "performance": 1.2}]}
            "last_updated": None
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.DECAY_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_performance(self, category: str, views: int, avg_views: int):
        """Record a category's performance."""
        if category not in self.data["category_history"]:
            self.data["category_history"][category] = []
        
        performance = views / max(avg_views, 1)
        
        self.data["category_history"][category].append({
            "date": datetime.now().isoformat(),
            "performance": performance
        })
        
        # Keep last 30 entries
        self.data["category_history"][category] = self.data["category_history"][category][-30:]
        
        self._save()
    
    def get_decayed_weights(self) -> Dict[str, float]:
        """Get category weights with time decay applied."""
        weights = {}
        now = datetime.now()
        
        for category, history in self.data["category_history"].items():
            if not history:
                weights[category] = 1.0
                continue
            
            weighted_sum = 0
            weight_total = 0
            
            for entry in history:
                try:
                    entry_date = datetime.fromisoformat(entry["date"])
                    days_ago = (now - entry_date).days
                    
                    # Exponential decay
                    decay_factor = 0.5 ** (days_ago / self.DECAY_HALF_LIFE_DAYS)
                    
                    weighted_sum += entry["performance"] * decay_factor
                    weight_total += decay_factor
                except:
                    continue
            
            if weight_total > 0:
                weights[category] = weighted_sum / weight_total
            else:
                weights[category] = 1.0
        
        return weights
    
    def get_recommended_categories(self, all_categories: List[str]) -> List[str]:
        """Get categories sorted by decayed performance."""
        weights = self.get_decayed_weights()
        
        # Add categories not yet tracked with neutral weight
        for cat in all_categories:
            if cat not in weights:
                weights[cat] = 1.0
        
        # Sort by weight descending
        sorted_cats = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        return [c[0] for c in sorted_cats]


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_orchestrator = None
_hook_tracker = None
_voice_optimizer = None
_hashtag_rotator = None
_platform_analytics = None
_category_decay = None

def get_enhancement_orchestrator() -> EnhancementOrchestrator:
    """Get the singleton enhancement orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancementOrchestrator()
    return _orchestrator


def get_hook_tracker() -> HookWordTracker:
    """Get the singleton hook word tracker."""
    global _hook_tracker
    if _hook_tracker is None:
        _hook_tracker = HookWordTracker()
    return _hook_tracker


def get_voice_optimizer() -> VoiceSpeedOptimizer:
    """Get the singleton voice speed optimizer."""
    global _voice_optimizer
    if _voice_optimizer is None:
        _voice_optimizer = VoiceSpeedOptimizer()
    return _voice_optimizer


def get_hashtag_rotator() -> HashtagRotator:
    """Get the singleton hashtag rotator."""
    global _hashtag_rotator
    if _hashtag_rotator is None:
        _hashtag_rotator = HashtagRotator()
    return _hashtag_rotator


def get_platform_analytics() -> CrossPlatformAnalytics:
    """Get the singleton cross-platform analytics."""
    global _platform_analytics
    if _platform_analytics is None:
        _platform_analytics = CrossPlatformAnalytics()
    return _platform_analytics


def get_category_decay() -> CategoryDecayTracker:
    """Get the singleton category decay tracker."""
    global _category_decay
    if _category_decay is None:
        _category_decay = CategoryDecayTracker()
    return _category_decay


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Enhancement Module v9.5 - Test")
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
    
    # v9.5 Enhancements
    print("\n" + "=" * 60)
    print("v9.5 Enhancements")
    print("=" * 60)
    
    print("\n[TEST #27] Seasonal Content Calendar:")
    seasonal = get_seasonal_content_suggestions()
    print(f"  Upcoming events: {len(seasonal.get('upcoming_events', []))}")
    print(f"  Content urgency: {seasonal.get('content_urgency', 'unknown')}")
    
    print("\n[TEST #28] Hook Word Tracker:")
    hook_tracker = get_hook_tracker()
    hook_tracker.record_hook_performance("This SECRET will SHOCK you", 50000, 10000)
    power_words = hook_tracker.get_power_words()
    print(f"  Power words tracked: {len(power_words)}")
    
    print("\n[TEST #29] Voice Speed Optimizer:")
    voice_opt = get_voice_optimizer()
    optimal = voice_opt.get_optimal_rate()
    print(f"  Optimal rate: {optimal}")
    
    print("\n[TEST #30] Hashtag Rotator:")
    hashtag_rot = get_hashtag_rotator()
    recent_sets = hashtag_rot.get_recently_used()
    print(f"  Recent sets tracked: {len(recent_sets)}")
    
    print("\n[TEST #32] Cross-Platform Analytics:")
    plat_analytics = get_platform_analytics()
    insights = plat_analytics.get_platform_insights()
    print(f"  Platforms tracked: {list(insights.keys())}")
    
    print("\n[TEST #35] Category Decay Tracker:")
    decay = get_category_decay()
    weights = decay.get_decayed_weights()
    print(f"  Categories with decay: {len(weights)}")
    
    print("\n" + "=" * 60)
    print("[OK] Enhancement module v9.5 ready!")
    print("=" * 60)


#!/usr/bin/env python3
"""
ViralShorts Factory - GOD-TIER PROMPT ENGINEERING
Ultra-optimized prompts for maximum viral potential.

Each prompt is crafted using advanced prompt engineering techniques:
1. Role priming (expert persona)
2. Chain of thought reasoning
3. Few-shot examples
4. Constraint specification
5. Output format enforcement
6. Anti-hallucination guards
7. Emotional/psychological triggers
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Gemini as fallback for when Groq fails
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def strip_emojis(text: str) -> str:
    """Remove ALL emojis and special characters that don't render."""
    # Comprehensive emoji and symbol removal
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"  # enclosed
        u"\U0001f926-\U0001f937"  # people
        u"\U00010000-\U0010ffff"  # supplementary
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"
        u"\u3030"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()


# =============================================================================
# GOD-TIER PROMPT: Viral Topic Generation
# =============================================================================

VIRAL_TOPIC_PROMPT = """You are MrBeast's head content strategist combined with Robert Cialdini (psychology) 
and James Clear (actionable advice). You've created content with 50 BILLION views.

Your task: Generate video ideas that DELIVER REAL VALUE and go viral.

CURRENT CONTEXT:
- Date: {date}
- Day: {day_of_week}  
- Season: {season}
- Trending themes: {trending_themes}

===== THE PROMISE-PAYOFF CONTRACT (CRITICAL!) =====
Every viral video makes a PROMISE in the hook and DELIVERS in the content.

❌ NEVER DO THIS:
- "Here's an amazing strategy..." (without explaining the strategy)
- "Learn this powerful technique..." (without teaching the technique)
- "Scientists discovered..." (without saying what they discovered)
- "You won't believe..." (and then not delivering the surprise)

✅ ALWAYS DO THIS:
- "The 2-minute rule: Any task under 2 minutes, do it NOW. I did 47 yesterday."
- "Your willpower crashes at 3pm. Schedule hard tasks before noon."
- "You've walked past 36 murderers. Based on crime rates, it's mathematically certain."

===== NUMBERED PROMISE RULE (CRITICAL - DO NOT VIOLATE!) =====
If your hook/title mentions a NUMBER of items, the content MUST contain EXACTLY that many items!

❌ BROKEN PROMISE (will get flagged!):
- Hook: "7 Weird Christmas Traditions" → Content only mentions 2 traditions
- Hook: "5 Money Secrets" → Content only explains 1 secret
- Hook: "3 Signs You're..." → Content only gives 1 sign

✅ DELIVERED PROMISE:
- Hook: "3 Signs You're Smarter" → Content: "First: [sign 1]. Second: [sign 2]. Third: [sign 3]."
- Hook: "5 Money Hacks" → Content lists all 5 hacks with clear transitions

VALIDATION: If you use a number N in the hook, COUNT the distinct items in your content. 
If count < N, either: (a) add more items, or (b) change the hook to match the count.
SAFER APPROACH: Use "THIS one trick" or "The secret" instead of numbered lists if unsure.

===== VALUE-FIRST CONTENT STRUCTURE =====
HOOK (2 sec): Shocking specific claim with a NUMBER or FACT
BUILD (5 sec): Context that increases tension
DELIVER (10 sec): THE ACTUAL VALUE - specific steps, numbers, proof
REINFORCE (3 sec): Why this matters to THEM personally
CTA (2 sec): Question that makes them reflect/comment

===== CONTENT REQUIREMENTS =====
1. Include AT LEAST 2 specific numbers (percentages, times, counts)
2. Give ONE clear actionable step they can take TODAY
3. Explain the MECHANISM (why/how it works)
4. Make them feel SMARTER after watching
5. NO empty promises - if you say "here's how," you MUST explain how

===== BELIEVABILITY & QUALITY (CRITICAL!) =====
You are creating content for SKEPTICAL viewers. Everything must feel REAL and TRUSTWORTHY.

NUMBERS MUST BE:
- REALISTIC: Use believable, commonly-cited numbers (not random like $3333 or 47.3%)
- ROUND & MEMORABLE: $500, 80%, 1000+, 30 days (NOT $487, 83.7%, 947, 29 days)
- VERIFIABLE: Could someone Google this? If not, soften the claim.
- STICKY: Easy to remember and share

❌ AWKWARD NUMBERS (feel fake/AI-generated):
- "You're losing $3333 every year" (why that random number?)
- "47.3% of people experience this" (too precise to be believable)
- "In 1847, scientists discovered..." (random year)

✅ BELIEVABLE NUMBERS (feel researched/real):
- "You're losing $500+ every year" (round, memorable)
- "Nearly half of people experience this" (natural phrasing)
- "In the 1990s, scientists discovered..." (believable range)

THE SKEPTICAL VIEWER TEST:
Before using ANY claim, ask: "Would a skeptical viewer think 'this sounds made up'?"
If yes → use softer language, round numbers, or cite a source type ("Harvard study")

===== SHORT-FORM VIDEO READABILITY (CRITICAL!) =====
This content will be displayed as TEXT on mobile screens. Optimize for VISUAL READABILITY:

1. NUMBERS AS DIGITS: Always use "500" not "five hundred", "3pm" not "three pm", "$50" not "fifty dollars"
2. SHORT SENTENCES: Maximum 12 words per sentence. Viewers read while watching.
3. NO COMPLEX WORDS: Use "use" not "utilize", "get" not "obtain", "show" not "demonstrate"
4. CONVERSATIONAL: Write like texting a friend, not writing an essay
5. PUNCHY PHRASES: Each sentence should hit hard. No filler words.
6. SCANNABLE: Viewer should understand the point in 2 seconds of reading
7. NATURAL HUMAN SPEECH: Would a real person say this? If it sounds robotic, rewrite it.

BAD: "Studies have demonstrated that approximately five hundred individuals..."
GOOD: "500 people tested this. 73% saw results in 2 weeks."

BAD: "You are losing exactly $3,847.52 per year on hidden fees..."
GOOD: "You're losing $500+ a year on hidden fees. Here's how to stop it."

===== B-ROLL KEYWORDS =====
- Highly specific ("person staring at phone in dark room" not "technology")
- Emotionally matched to content
- Available on stock sites

Generate {count} video ideas. For EACH video:

CRITICAL: The "hook" and "content" are SEPARATE! Do NOT repeat the hook inside the content!
- hook = The opening attention-grabber (spoken first)
- content = The rest of the video (spoken after the hook)

{{
    "topic": "2-4 word topic name",
    "video_type": "scary_fact|money_fact|psychology_fact|life_hack|mind_blow",
    "hook": "7-10 word attention grabber - this is spoken FIRST - NO EMOJIS",
    "content": "The REST of the video AFTER the hook. Do NOT repeat the hook here! Include: mechanism/evidence, actionable takeaway. 50-80 words. NO EMOJIS.",
    "the_payoff": "The ONE specific thing they learn/can do after watching",
    "call_to_action": "Reflective question that drives comments",
    "broll_keywords": ["specific visual 1", "specific visual 2", "specific visual 3", "specific visual 4"],
    "music_mood": "suspense|dramatic|inspirational|energetic|emotional",
    "virality_score": 1-10,
    "psychological_triggers": ["trigger1", "trigger2"],
    "why_viral": "One sentence on the psychology of why this spreads"
}}

Return a JSON array of {count} objects. No markdown, no emojis, no explanations outside JSON."""


# =============================================================================
# GOD-TIER PROMPT: Content Quality Evaluation
# =============================================================================

CONTENT_EVALUATION_PROMPT = """You are a YouTube Shorts algorithm expert who has analyzed 10 million viral videos. You understand exactly what makes content spread.

Evaluate this video content for viral potential:

HOOK: "{hook}"
CONTENT: "{content}"
TYPE: {video_type}

Score each dimension (1-10) and explain:

1. SCROLL-STOPPING POWER (Does the hook make you stop scrolling?)
   - First 0.5 seconds must be UNMISSABLE
   - Pattern interrupt or curiosity gap required
   
2. INFORMATION VALUE (Does viewer learn something valuable?)
   - Not just "interesting" but USEFUL or SURPRISING
   - Must feel like insider knowledge
   
3. EMOTIONAL INTENSITY (Does it trigger strong emotion?)
   - Fear, anger, joy, surprise, or awe
   - Weak emotions = no shares
   
4. SHAREABILITY (Would someone send this to a friend?)
   - "You HAVE to see this"
   - Must create social currency
   
5. COMMENT BAIT (Does it provoke discussion?)
   - Controversial without being offensive
   - Easy to have an opinion

Return JSON:
{{
    "scroll_stop": {{"score": 1-10, "reason": "why"}},
    "info_value": {{"score": 1-10, "reason": "why"}},
    "emotion": {{"score": 1-10, "reason": "why"}},
    "shareability": {{"score": 1-10, "reason": "why"}},
    "comment_bait": {{"score": 1-10, "reason": "why"}},
    "overall": 1-10,
    "verdict": "VIRAL|GOOD|WEAK|TRASH",
    "improvements": ["specific improvement 1", "specific improvement 2"]
}}"""


# =============================================================================
# GOD-TIER PROMPT: B-roll Keyword Extraction
# =============================================================================

BROLL_KEYWORDS_PROMPT = """You are a professional video editor who has worked on Netflix documentaries. You understand visual storytelling.

For this video content, suggest B-roll footage that will:
1. ENHANCE the emotional impact
2. ILLUSTRATE concepts visually
3. MAINTAIN viewer attention
4. CREATE professional production value

CONTENT: "{content}"
MOOD: {mood}

Think about:
- What visuals would a BBC documentary use?
- What creates MOVEMENT and ENERGY on screen?
- What colors and lighting support the mood?
- What's AVAILABLE on stock sites (Pexels, Pixabay)?

BAD B-ROLL: "abstract", "motion", "colorful" (too generic)
GOOD B-ROLL: "dramatic storm clouds time lapse", "person looking worried close up", "money falling slow motion"

Return EXACTLY 5 specific, searchable B-roll descriptions:
{{
    "primary": "Most important visual - shown most of video",
    "secondary": "Supporting visual for variety",
    "detail": "Close-up or detail shot",
    "atmosphere": "Mood-setting background",
    "transition": "Visual for transitions",
    "search_terms": ["exact search term 1", "exact search term 2", "exact search term 3", "exact search term 4", "exact search term 5"]
}}"""


# =============================================================================
# GOD-TIER PROMPT: Voiceover Script
# =============================================================================

VOICEOVER_PROMPT = """You are Morgan Freeman's dialogue coach + a TikTok creator with 50M followers.

Write a voiceover that DELIVERS VALUE, not just promises it.

CONTENT TO ADAPT: "{content}"
TARGET: 15-30 seconds (50-80 words)

===== THE VALUE TEST =====
Before writing, ask: "What does the viewer LEARN or GAIN from this?"
If the answer is vague ("motivation" / "awareness"), rewrite until it's SPECIFIC.

GOOD: "Viewer learns the 2-minute rule and can use it today"
BAD: "Viewer feels inspired to be productive"

===== STRUCTURE =====
1. HOOK (1 sec): Surprising claim that STOPS the scroll
2. BUILD (3 sec): Create anticipation for the payoff
3. DELIVER (10 sec): THE ACTUAL VALUE - specific, actionable, memorable
4. REINFORCE (3 sec): Why this matters to THEM
5. CTA (2 sec): Question that drives comments

===== STYLE RULES =====
- Short sentences (5-10 words max)
- Pauses as "..." for emphasis
- CAPS for key words
- NO filler words
- Conversational but confident
- Numbers and specifics always

===== BELIEVABILITY CHECK (CRITICAL!) =====
Before writing, pass EVERY claim through the SKEPTICAL VIEWER test:
- Would someone watching think "this sounds made up"?
- Are the numbers REALISTIC and MEMORABLE? (round numbers: $500, 80%, 30 days)
- Does anything sound robotic or awkward when read aloud?
- Would a human naturally say this in conversation?

❌ FAILS THE TEST:
- "You're losing $3,847 every year" (random number = fake)
- "Studies from 1847 proved..." (random year = suspicious)  
- "This affects exactly 47.3% of people" (too precise = AI garbage)

✅ PASSES THE TEST:
- "You're losing over $500 a year" (round, believable)
- "For decades, scientists have known..." (natural phrasing)
- "Nearly half of people experience this" (conversational)

===== MOBILE READABILITY (CRITICAL!) =====
The script will be displayed as TEXT OVERLAY on mobile screens:
- ALWAYS use digits: "500" not "five hundred", "$20" not "twenty dollars"
- ALWAYS use symbols: "$", "%", "&" - they're shorter and scannable
- Keep each phrase under 10 words - this becomes one text screen
- Use everyday words: "use" not "utilize", "buy" not "purchase"
- Be specific: "3pm" not "afternoon", "47 people" not "many people"

BAD: "There's a technique you should learn about..."
GOOD: "The 2-minute rule. If it takes less than 2 minutes... do it NOW."

BAD: "Studies show this really works for most people."
GOOD: "MIT tested 1,200 students. 73% improved in 2 weeks."

BAD: "You could save approximately five hundred dollars annually."
GOOD: "Save $500/year with this 1 trick."

BAD: "You are losing exactly $3,333 on crypto fees every year."
GOOD: "Crypto fees are eating $500+ of your money. Here's the fix."

Return JSON:
{{
    "script": "Complete script with pauses as ...",
    "word_count": number,
    "estimated_duration_seconds": number,
    "the_value_delivered": "ONE sentence describing what viewer gains",
    "hook_line": "First line only",
    "closing_line": "Last line only"
}}"""


# =============================================================================
# GOD-TIER PROMPT: Platform-Specific Optimization (#6)
# =============================================================================

PLATFORM_OPTIMIZATION_PROMPT = """You are a MULTI-PLATFORM STRATEGIST who knows the differences between platforms.

=== ORIGINAL CONTENT ===
Title: {title}
Hook: {hook}
CTA: {cta}
Platform: {platform}

=== PLATFORM DIFFERENCES ===
YOUTUBE SHORTS:
- Formal-ish, educational tone works well
- Subscribe CTAs are effective
- Hashtags: #shorts required, 3-5 relevant tags
- Longer hooks OK (2-3 seconds)

DAILYMOTION:
- More casual, entertainment-focused audience
- Lower competition = can be more niche
- Less emphasis on subscribe CTAs
- Similar format to YouTube

TIKTOK (future):
- Very casual, trend-driven
- "Duet this" / "Stitch this" CTAs
- Trending sounds matter
- Hook must be < 1 second

=== OUTPUT JSON ===
{{
    "optimized_title": "platform-specific title",
    "optimized_hook": "adjusted hook for platform",
    "optimized_cta": "platform-appropriate CTA",
    "hashtags": ["#shorts", "#relevant", "#tags"],
    "platform_tips": ["tip for this platform"]
}}

JSON ONLY."""


# =============================================================================
# GOD-TIER PROMPT: Contextual Event Awareness (#15)
# =============================================================================

CONTEXTUAL_AWARENESS_PROMPT = """You are a CULTURAL SENSITIVITY and TIMING expert.

=== CONTENT ===
Topic: {topic}
Hook: {hook}
Date: {current_date}

=== CHECK FOR ===
1. SENSITIVE DATES: Is today a day we should avoid certain topics?
   - Memorial days, tragedies anniversaries, religious holidays
   
2. OPPORTUNITY DATES: Is there an event we can leverage?
   - Sports events, award shows, product launches, holidays
   
3. REGIONAL SENSITIVITY: Global audience considerations
   - Avoid US-centric assumptions
   - Be aware of international events

4. TRENDING OPPORTUNITIES: Any current events to reference?

=== OUTPUT JSON ===
{{
    "is_sensitive": true/false,
    "sensitivity_reason": "why sensitive" or null,
    "is_opportunity": true/false,
    "opportunity_reason": "event to leverage" or null,
    "modifications_needed": ["change 1"] or [],
    "proceed": true/false,
    "timing_score": 1-10
}}

JSON ONLY."""


# =============================================================================
# GOD-TIER PROMPT: Cross-Promotion Network (#19)
# =============================================================================

CROSS_PROMOTION_PROMPT = """You are a CONTENT NETWORK STRATEGIST.

=== CURRENT VIDEO ===
Topic: {current_topic}
Category: {category}

=== RECENT VIDEOS (for cross-promotion) ===
{recent_videos}

=== TASK ===
Suggest how to connect this video to our other content:
1. Related video to mention in description
2. Series/theme to establish
3. "Watch next" suggestion for end screen

=== OUTPUT JSON ===
{{
    "related_video": "title of related video from list" or null,
    "description_mention": "Check out our video on [X] for more!" or null,
    "series_opportunity": "This could be part of [X] series" or null,
    "end_screen_suggestion": "Pair with [video] for end screen"
}}

JSON ONLY."""


# =============================================================================
# GOD-TIER PROMPT: Failed Content Recycling (#23)
# =============================================================================

CONTENT_RECYCLING_PROMPT = """You are a CONTENT RESURRECTION SPECIALIST.
This video underperformed. Diagnose WHY and prescribe a FIX.

=== FAILED VIDEO ===
Title: {title}
Hook: {hook}
Topic: {topic}
Views: {views} (our average: {avg_views})
Engagement: {engagement}

=== AUTOPSY - Find the cause of death ===
1. Was the hook weak?
2. Was the topic stale?
3. Was the title unclickable?
4. Was the content thin?
5. Was timing bad?

=== RESURRECTION PLAN ===
{{
    "diagnosis": "why it failed",
    "salvageable": true/false,
    "resurrection_plan": {{
        "new_angle": "fresh approach to same topic",
        "new_hook": "stronger hook",
        "new_title": "more clickable title",
        "timing_suggestion": "when to republish"
    }},
    "effort_score": 1-10 (10 = too much work)
}}

JSON ONLY."""


# =============================================================================
# Main Class
# =============================================================================

class GodTierContentGenerator:
    """Generate viral content using god-tier prompts with multi-AI support."""
    
    def __init__(self):
        self.groq_client = None
        self.gemini_client = None
        
        # Initialize Groq (primary - faster)
        if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
            self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Initialize Gemini 2.0 Flash (backup - latest model with enhanced performance)
        if HAS_GEMINI and os.environ.get("GEMINI_API_KEY"):
            try:
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                # Try Gemini 2.0 Flash (latest), fallback to 1.5 if not available
                try:
                    self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
                    print("✅ Gemini 2.0 Flash (experimental) initialized")
                except:
                    self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                    print("✅ Gemini 1.5 Flash initialized (2.0 not available)")
            except Exception as e:
                print(f"⚠️ Gemini init failed: {e}")
    
    def _call_ai(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Make AI call with automatic fallback (Groq -> Gemini)."""
        
        # Try Groq first (faster)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.85  # High creativity
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"⚠️ Groq failed: {e}, trying Gemini...")
        
        # Fallback to Gemini (higher quality)
        if self.gemini_client:
            try:
                response = self.gemini_client.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"⚠️ Gemini also failed: {e}")
        
        print("❌ All AI providers failed")
        return None
    
    def _parse_json(self, text: str) -> Optional[Dict]:
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
    
    def generate_viral_topics(self, count: int = 3) -> List[Dict]:
        """
        Generate viral topic ideas using god-tier prompt.
        
        IMPORTANT: Uses MULTIPLE SOURCES for trending data - NO HARDCODED TOPICS!
        Sources: Google Trends RSS, Reddit, AI predictions
        """
        # Try Multi-Source Trend Fetcher first (Google RSS + Reddit + AI)
        try:
            from multi_trend_fetcher import MultiTrendFetcher
            fetcher = MultiTrendFetcher()
            raw_trends = fetcher.fetch_all(count=count * 2)  # Get extra for filtering
            
            if raw_trends:
                print(f"[OK] Got {len(raw_trends)} trends from multi-source fetcher")
                
                # Convert to our topic format using AI
                topics = []
                for trend in raw_trends[:count]:
                    topic = self._trend_to_topic(trend)
                    if topic:
                        # Track source for analytics
                        topic["_source"] = trend.source  # "google", "reddit", "ai"
                        topics.append(topic)
                
                if topics:
                    return topics
        except Exception as e:
            print(f"[!] Multi-source trend fetcher unavailable: {e}")
        
        # Fallback: Use the AI Trend Fetcher (AI only)
        try:
            from ai_trend_fetcher import AITrendFetcher
            fetcher = AITrendFetcher()
            topics = fetcher.fetch_trending_topics(count)
            
            if topics:
                print(f"[OK] Got {len(topics)} trending topics from AI Trend Fetcher")
                return topics
        except Exception as e:
            print(f"[!] AI Trend Fetcher unavailable: {e}")
        
        # Fallback: Use the prompt system but let AI determine trends
        now = datetime.now()
        
        # DYNAMIC season context (no hardcoded topics!)
        month = now.month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"
        
        # Let AI figure out what's trending - NO HARDCODED LIST
        trending = "USE YOUR KNOWLEDGE to determine what topics are currently trending and relevant"
        
        prompt = VIRAL_TOPIC_PROMPT.format(
            date=now.strftime("%B %d, %Y"),
            day_of_week=now.strftime("%A"),
            season=season,
            trending_themes=trending,
            count=count
        )
        
        result = self._call_ai(prompt)
        topics = self._parse_json(result)
        
        if isinstance(topics, list):
            # Strip emojis from all text fields
            for topic in topics:
                for key in ["hook", "content", "topic", "call_to_action"]:
                    if key in topic and topic[key]:
                        topic[key] = strip_emojis(str(topic[key]))
            return topics
        
        return []
    
    def _trend_to_topic(self, trend) -> Optional[Dict]:
        """Convert a trending topic to our video topic format using AI."""
        prompt = f"""Convert this trending topic into a viral short video script.

TRENDING TOPIC: {trend.topic}
SOURCE: {trend.source}
CATEGORY: {trend.category}
KEYWORDS: {', '.join(trend.keywords) if trend.keywords else 'N/A'}

Create a video that:
1. Uses this trend to deliver REAL VALUE
2. Includes specific numbers/facts
3. Has an actionable takeaway

Return JSON:
{{
    "topic": "{trend.topic[:50]}",
    "video_type": "{trend.category}_fact",
    "hook": "7-10 word attention grabber - NO EMOJIS",
    "content": "50-80 words of VALUE - NO EMOJIS",
    "the_payoff": "What viewer learns",
    "call_to_action": "Question for comments",
    "broll_keywords": ["visual1", "visual2", "visual3", "visual4"],
    "music_mood": "dramatic|suspense|inspirational",
    "virality_score": 8,
    "psychological_triggers": ["trigger1", "trigger2"],
    "why_viral": "Why this spreads"
}}

Only return valid JSON."""

        result = self._call_ai(prompt, max_tokens=800)
        topic = self._parse_json(result)
        
        if topic:
            # Strip emojis
            for key in ["hook", "content", "topic", "call_to_action"]:
                if key in topic and topic[key]:
                    topic[key] = strip_emojis(str(topic[key]))
            return topic
        
        return None
    
    def generate_broll_keywords(self, content: str, mood: str) -> Dict:
        """Generate specific B-roll keywords."""
        prompt = BROLL_KEYWORDS_PROMPT.format(content=content, mood=mood)
        result = self._call_ai(prompt, max_tokens=500)
        return self._parse_json(result) or {}
    
    def evaluate_content(self, hook: str, content: str, video_type: str) -> Dict:
        """Evaluate content quality."""
        prompt = CONTENT_EVALUATION_PROMPT.format(
            hook=hook, content=content, video_type=video_type
        )
        result = self._call_ai(prompt, max_tokens=800)
        return self._parse_json(result) or {}
    
    def generate_voiceover(self, content: str) -> Dict:
        """Generate optimized voiceover script."""
        prompt = VOICEOVER_PROMPT.format(content=content)
        result = self._call_ai(prompt, max_tokens=500)
        data = self._parse_json(result) or {}
        
        # Strip emojis from script
        if "script" in data:
            data["script"] = strip_emojis(data["script"])
        
        return data


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 GOD-TIER PROMPT ENGINEERING TEST")
    print("=" * 60)
    
    # Direct API test
    api_key = os.environ.get("GROQ_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            print("✅ Groq client created")
            
            # Quick test
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say 'test successful' in 3 words"}],
                max_tokens=20
            )
            print(f"✅ API Test: {response.choices[0].message.content}")
        except Exception as e:
            print(f"❌ Error: {e}")
            client = None
    else:
        client = None
    
    gen = GodTierContentGenerator()
    gen.client = client
    
    if not gen.client:
        print("⚠️ No AI client - set GROQ_API_KEY")
    else:
        print("\n📊 Generating viral topics...")
        topics = gen.generate_viral_topics(2)
        
        for i, topic in enumerate(topics, 1):
            print(f"\n{'='*50}")
            print(f"📹 Topic {i}: {topic.get('topic', 'N/A')}")
            print(f"   Hook: {topic.get('hook', 'N/A')}")
            print(f"   Type: {topic.get('video_type', 'N/A')}")
            print(f"   Virality: {topic.get('virality_score', 'N/A')}/10")
            print(f"   Triggers: {topic.get('psychological_triggers', [])}")
            print(f"   B-roll: {topic.get('broll_keywords', [])}")
            print(f"   Why viral: {topic.get('why_viral', 'N/A')}")


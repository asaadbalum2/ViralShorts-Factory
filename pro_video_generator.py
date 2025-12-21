#!/usr/bin/env python3
"""
ViralShorts Factory - PROFESSIONAL Video Generator v7.1
========================================================

100% AI-DRIVEN - NO HARDCODING!
ENFORCED VARIETY - Every video in a batch MUST be different!

Core Philosophy:
- Master Prompt -> AI -> Answer -> Evaluation -> AI -> Refined Answer
- AI decides: video type, phrase count, content length, music mood, voice style
- VARIETY ENFORCED: Track generated topics/voices/music to prevent repetition
- Strategic Selection: Score all videos and pick BEST for YouTube
"""

import os
import sys
import re
import json
import asyncio
import random
import time
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import requests

# Core imports
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, ImageClip, CompositeAudioClip,
    ColorClip
)
from moviepy.video.VideoClip import VideoClip
import moviepy.video.fx.all as vfx

from PIL import Image, ImageDraw, ImageFont, ImageFilter
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import edge_tts

# Constants (only technical, not content!)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BROLL_DIR = Path("./assets/broll")
BROLL_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ========================================================================
# BATCH VARIETY TRACKER - Prevents repetition across batch runs
# ========================================================================
@dataclass
class BatchTracker:
    """Tracks what's been generated in this batch to enforce variety."""
    used_categories: List[str] = field(default_factory=list)
    used_topics: List[str] = field(default_factory=list)
    used_voices: List[str] = field(default_factory=list)
    used_music: List[str] = field(default_factory=list)
    video_scores: List[Tuple[str, float, Dict]] = field(default_factory=list)
    
    def add_video(self, path: str, score: float, metadata: Dict):
        """Add a generated video with its score."""
        self.video_scores.append((path, score, metadata))
    
    def get_best_video_for_youtube(self) -> Optional[Tuple[str, Dict]]:
        """Get the highest-scoring video for YouTube upload."""
        if not self.video_scores:
            return None
        # Sort by score descending
        sorted_videos = sorted(self.video_scores, key=lambda x: x[1], reverse=True)
        best_path, best_score, best_meta = sorted_videos[0]
        safe_print(f"\n[SELECTION] Best video for YouTube: score={best_score}/10")
        safe_print(f"   Path: {best_path}")
        return (best_path, best_meta)
    
    def get_all_videos(self) -> List[Tuple[str, Dict]]:
        """Get all videos for Dailymotion upload."""
        return [(path, meta) for path, score, meta in self.video_scores]


# Global batch tracker (reset for each batch run)
BATCH_TRACKER = BatchTracker()


def safe_print(msg: str):
    """Print with fallback for Windows encoding issues."""
    try:
        print(msg)
    except UnicodeEncodeError:
        clean = re.sub(r'[^\x00-\x7F]+', '', msg)
        print(clean)


def strip_emojis(text: str) -> str:
    """Remove emojis."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()


# ========================================================================
# ALL AVAILABLE OPTIONS - AI picks from these, variety enforced
# ========================================================================
# Base categories - AI will expand/suggest from these + current trends
BASE_CATEGORIES = [
    "psychology", "finance", "productivity", "health", 
    "relationships", "science", "technology", "motivation",
    "life_hacks", "history", "statistics", "mysteries"
]

def get_ai_trending_categories(groq_key: str = None) -> List[str]:
    """
    Ask AI for currently trending content categories.
    Combines base categories with AI-suggested trending ones.
    """
    if not groq_key:
        groq_key = os.environ.get("GROQ_API_KEY")
    
    if not groq_key:
        return BASE_CATEGORIES
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": f"""What are the TOP 5 trending content categories for viral short-form videos RIGHT NOW?

Consider:
- Current events and news cycles
- Seasonal trends
- Social media trending topics
- What's capturing attention today

Base categories (keep if still relevant): {BASE_CATEGORIES}

Return a JSON array of 8-12 category names (single words or short phrases, lowercase, underscores for spaces).
Example: ["ai_news", "psychology", "money_hacks", "relationship_tips", "health", "productivity"]

Return ONLY the JSON array, nothing else."""}],
                "temperature": 0.8,
                "max_tokens": 200
            },
            timeout=10
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                categories = json.loads(json_match.group())
                if isinstance(categories, list) and len(categories) >= 5:
                    safe_print(f"   [OK] AI suggested categories: {categories[:5]}...")
                    return categories
    except Exception as e:
        pass
    
    return BASE_CATEGORIES

# Will be populated dynamically by AI
ALL_CATEGORIES = BASE_CATEGORIES  # Fallback, gets updated at runtime

# NOTE: Voice names are Edge TTS technical identifiers (cannot be AI-generated)
# AI selects the STYLE (energetic, calm, etc.), which maps to these voices
# The rate adjustments are tuned for optimal narration pacing
# Edge TTS Available Voices - AI will select dynamically based on content
# This is just a reference list for validation, NOT the selection logic
EDGE_TTS_VOICES = [
    'en-US-AriaNeural', 'en-US-JennyNeural', 'en-US-GuyNeural', 'en-US-DavisNeural',
    'en-US-ChristopherNeural', 'en-US-EricNeural', 'en-US-MichelleNeural', 
    'en-US-RogerNeural', 'en-US-SteffanNeural', 'en-US-SaraNeural',
    'en-AU-WilliamNeural', 'en-AU-NatashaNeural',
    'en-GB-RyanNeural', 'en-GB-SoniaNeural', 'en-GB-LibbyNeural',
    'en-CA-LiamNeural', 'en-CA-ClaraNeural',
    'en-IE-ConnorNeural', 'en-IN-NeerjaNeural', 'en-NZ-MitchellNeural',
]

# Default rate adjustments (AI can override)
DEFAULT_VOICE_RATES = {
    'energetic': '+8%', 'calm': '-5%', 'mysterious': '-3%', 
    'authoritative': '+0%', 'friendly': '+3%', 'dramatic': '-2%',
    'professional': '+0%', 'casual': '+5%', 'warm': '+0%',
}

# NOTE: These are MOOD LABELS, not hardcoded tracks!
# AI selects the mood → ai_music_selector.py uses AI to find matching music
# The actual track selection is dynamic and AI-driven
ALL_MUSIC_MOODS = [
    'upbeat',        # Fun, positive content
    'dramatic',      # Scary facts, shocking reveals
    'mysterious',    # Mysteries, unknown facts
    'inspirational', # Motivation, success
    'chill',         # Calm explanations, tips
    'intense',       # Urgent, action-oriented
    'energetic',     # High energy, productivity
    'emotional',     # Personal stories, psychology
    'tech',          # Technology, science
    'professional',  # Finance, business
]

# Keep for backward compatibility
ALL_MUSIC = {mood: mood for mood in ALL_MUSIC_MOODS}


class MasterAI:
    """
    100% AI-Driven Content System with ENFORCED VARIETY
    
    Uses BatchTracker to ensure no repetition in category/topic/voice/music.
    """
    
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.gemini_model = None
        
        if self.groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.groq_key)
                safe_print("[OK] Groq AI initialized")
            except Exception as e:
                safe_print(f"[!] Groq init failed: {e}")
        
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                # Try latest experimental model first, fallback to stable
                try:
                    self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    safe_print("[OK] Gemini AI initialized (2.0-flash-exp)")
                except:
                    self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                    safe_print("[OK] Gemini AI initialized (2.0-flash)")
            except Exception as e:
                safe_print(f"[!] Gemini init failed: {e}")
    
    def call_ai(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.9) -> str:
        """Call AI with automatic fallback."""
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                safe_print(f"[!] Groq error: {e}")
        
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                safe_print(f"[!] Gemini error: {e}")
        
        return ""
    
    def parse_json(self, text: str) -> Dict:
        """Extract JSON from AI response."""
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            return {}
    
    # ========================================================================
    # STAGE 1: AI Decides What Type of Video to Create (with VARIETY ENFORCEMENT)
    # ========================================================================
    def stage1_decide_video_concept(self, hint: str = None, batch_tracker: BatchTracker = None) -> Dict:
        """
        AI decides EVERYTHING about the video concept.
        VARIETY ENFORCED: Avoids categories/topics already used in this batch.
        CATEGORIES: AI-suggested based on current trends.
        """
        safe_print("\n[STAGE 1] AI deciding video concept...")
        
        # Get AI-suggested trending categories (dynamic, not hardcoded!)
        trending_categories = get_ai_trending_categories(self.groq_key)
        
        # Build exclusion list from batch tracker
        exclude_categories = []
        exclude_topics = []
        if batch_tracker:
            exclude_categories = batch_tracker.used_categories[-5:]  # Last 5 used
            exclude_topics = batch_tracker.used_topics[-10:]  # Last 10 topics
        
        available_categories = [c for c in trending_categories if c not in exclude_categories]
        if not available_categories:
            available_categories = trending_categories  # Reset if all used
        
        unique_seed = f"{time.time()}_{random.random()}_{random.randint(10000,99999)}"
        hint_text = f"User hint: {hint}" if hint else "No specific hint - create something viral and valuable"
        
        exclude_text = ""
        if exclude_categories:
            exclude_text += f"\n\n**CRITICAL - DO NOT USE these categories (already used in batch):** {exclude_categories}"
        if exclude_topics:
            exclude_text += f"\n**DO NOT USE these topics (already used):** {exclude_topics[:5]}"
        
        # Build dynamic options from AI-driven lists
        music_options = ", ".join(ALL_MUSIC_MOODS)
        
        prompt = f"""You are a VIRAL CONTENT STRATEGIST for short-form video (YouTube Shorts, TikTok).
Your job is to decide what video to create that will get MAXIMUM views while delivering REAL value.

UNIQUE GENERATION ID: {unique_seed}
DATE: {time.strftime('%B %d, %Y, %A')}
{hint_text}
{exclude_text}

=== AVAILABLE CATEGORIES (pick ONE from this list ONLY) ===
{available_categories}

=== YOUR DECISION TASKS ===

1. **VIDEO CATEGORY**: Pick from the AVAILABLE list above (NOT the excluded ones!)
   
2. **SPECIFIC TOPIC**: Within that category, what specific topic?
   - Must be: Surprising, valuable, shareable, globally relevant
   - MUST BE UNIQUE - no generic topics!

3. **CONTENT LENGTH**: How many phrases/sections? (4-8)
   - Match length to content complexity

4. **VOICE STYLE**: What voice/energy for the narration?
   Options: energetic, calm, mysterious, authoritative, friendly, dramatic

5. **MUSIC MOOD**: What background music mood? (Match to content emotion!)
   Options: {music_options}

6. **TARGET DURATION**: How long should the video be?
   Options: 15-20s (quick fact), 25-35s (explained fact), 40-50s (mini-tutorial)

=== OUTPUT JSON ===
{{
    "category": "MUST be from available list",
    "specific_topic": "the specific topic (5-10 words) - BE CREATIVE AND UNIQUE",
    "why_this_topic": "why this will be viral and valuable",
    "phrase_count": 5,
    "voice_style": "energetic/calm/mysterious/etc",
    "music_mood": "upbeat/dramatic/mysterious/etc",
    "target_duration_seconds": 30,
    "global_relevance": "why this works worldwide"
}}

OUTPUT JSON ONLY. Be creative and strategic - NO REPETITION!"""

        response = self.call_ai(prompt, 800, temperature=0.98)  # Higher temp for variety
        result = self.parse_json(response)
        
        if result:
            category = result.get('category', '')
            topic = result.get('specific_topic', '')
            
            # Force variety if AI ignored exclusions
            if category in exclude_categories and available_categories:
                result['category'] = random.choice(available_categories)
                safe_print(f"   [VARIETY] Forced category change: {category} -> {result['category']}")
            
            # Track what we're using
            if batch_tracker:
                batch_tracker.used_categories.append(result.get('category', ''))
                batch_tracker.used_topics.append(result.get('specific_topic', ''))
            
            safe_print(f"   Category: {result.get('category', 'N/A')}")
            safe_print(f"   Topic: {result.get('specific_topic', 'N/A')}")
            safe_print(f"   Phrases: {result.get('phrase_count', 'N/A')}")
            safe_print(f"   Voice: {result.get('voice_style', 'N/A')}")
            safe_print(f"   Music: {result.get('music_mood', 'N/A')}")
            safe_print(f"   Duration: ~{result.get('target_duration_seconds', 'N/A')}s")
        
        return result
    
    # ========================================================================
    # STAGE 2: AI Creates the Content Based on Its Own Decisions
    # ========================================================================
    def stage2_create_content(self, concept: Dict) -> Dict:
        """AI creates the actual content based on the concept it decided."""
        safe_print("\n[STAGE 2] AI creating content...")
        
        phrase_count = concept.get('phrase_count', 5)
        
        prompt = f"""You are a VIRAL CONTENT CREATOR. Create the actual content for this video.

=== VIDEO CONCEPT (from Stage 1) ===
Category: {concept.get('category', 'educational')}
Topic: {concept.get('specific_topic', 'interesting fact')}
Why Viral: {concept.get('why_this_topic', 'valuable content')}
Target Duration: ~{concept.get('target_duration_seconds', 30)} seconds
Phrase Count: {phrase_count} phrases

=== CONTENT CREATION RULES ===

1. **VALUE DELIVERY**: Every phrase must add real information.
   - If you introduce a PROBLEM, you MUST provide a SPECIFIC SOLUTION
   - NO vague advice like "be better" - give SPECIFIC steps/numbers
   
2. **COMPREHENSIVENESS**: The content must be COMPLETE.
   - Viewer should feel they learned something ACTIONABLE
   - Include: specific techniques, numbers, timeframes, methods
   
3. **GLOBAL RELEVANCE**: Content must apply WORLDWIDE.
   - NO country-specific references
   - Universal human experiences and facts
   
4. **FORMAT**:
   - Use DIGITS for numbers (500$, 92%, 3x)
   - Each phrase: 10-20 words for readability
   - Build narrative: Hook -> Context -> Solution -> Payoff

=== CREATE EXACTLY {phrase_count} PHRASES ===
Structure:
1. HOOK (pattern interrupt, curiosity)
2-{phrase_count-1}. BUILD (problem, context, solution parts)
{phrase_count}. PAYOFF (transformation, call to action)

=== OUTPUT JSON ===
{{
    "phrases": [
        "Your attention-grabbing hook here",
        "The problem or context explained",
        "More detail or the solution",
        "The payoff or call to action"
    ],
    "specific_value": "What SPECIFIC action can viewer take after watching?",
    "problem_solved": "What problem did we solve?",
    "solution_given": "What specific solution did we provide?"
}}

CRITICAL: Do NOT include "Phrase 1:", "Phrase 2:" etc. in the phrases - just the text itself!
OUTPUT JSON ONLY. Make every phrase count!"""

        response = self.call_ai(prompt, 1200, temperature=0.85)
        result = self.parse_json(response)
        
        if result and result.get('phrases'):
            # Clean up any "Phrase X:" prefixes the AI might add
            cleaned_phrases = []
            for phrase in result.get('phrases', []):
                # Remove "Phrase 1:", "Phrase1:", "1:", "1." etc. prefixes
                import re
                cleaned = re.sub(r'^(Phrase\s*\d+\s*[:.]?\s*|\d+\s*[:.]?\s*)', '', phrase, flags=re.IGNORECASE).strip()
                cleaned_phrases.append(cleaned)
            result['phrases'] = cleaned_phrases
            result['concept'] = concept
            safe_print(f"   Created {len(result.get('phrases', []))} phrases")
            safe_print(f"   Value: {result.get('specific_value', 'N/A')[:60]}...")
        
        return result
    
    # ========================================================================
    # STAGE 3: AI Evaluates and Enhances the Content
    # ========================================================================
    def stage3_evaluate_enhance(self, content: Dict) -> Dict:
        """AI evaluates its own content and improves it."""
        safe_print("\n[STAGE 3] AI evaluating and enhancing...")
        
        phrases = content.get('phrases', [])
        
        prompt = f"""You are a VIRAL CONTENT QUALITY CONTROLLER.
Evaluate this content and IMPROVE any weaknesses.

=== CONTENT TO EVALUATE ===
{json.dumps(phrases, indent=2)}

Claimed Value: {content.get('specific_value', '')}
Problem Solved: {content.get('problem_solved', '')}
Solution Given: {content.get('solution_given', '')}

=== EVALUATION CRITERIA ===

1. **VALUE COMPLETENESS** (Critical!)
   - Does it deliver SPECIFIC, ACTIONABLE value?
   - Is the solution COMPLETE, not vague?
   - Can the viewer DO something specific after watching?
   
2. **HOOK STRENGTH**
   - Does phrase 1 create IRRESISTIBLE curiosity?
   - Would YOU stop scrolling for this?
   
3. **NARRATIVE FLOW**
   - Does each phrase build on the previous?
   - Is there a satisfying payoff?
   
4. **READABILITY**
   - All numbers as DIGITS?
   - Short, punchy sentences?
   - No jargon?

=== YOUR TASK ===
If ANY weakness is found, FIX IT in the improved phrases.
If the solution is vague, make it SPECIFIC with numbers/steps/techniques.

=== OUTPUT JSON ===
{{
    "evaluation_score": 1-10,
    "weaknesses_found": ["list of issues found"],
    "improvements_made": ["list of improvements"],
    "improved_phrases": [
        "The improved hook text here",
        "The improved second phrase here",
        "And so on for each phrase"
    ],
    "final_value_delivered": "What specific value does viewer get now?"
}}

CRITICAL: Do NOT include "Phrase 1:", "Improved phrase 1:" etc. - just the actual text!
OUTPUT JSON ONLY."""

        response = self.call_ai(prompt, 1000, temperature=0.7)
        result = self.parse_json(response)
        
        if result:
            # Clean up any prefixes from improved phrases
            improved = result.get('improved_phrases', content.get('phrases', []))
            cleaned_phrases = []
            for phrase in improved:
                import re
                cleaned = re.sub(r'^(Phrase\s*\d+\s*[:.]?\s*|Improved\s*(phrase)?\s*\d*\s*[:.]?\s*|\d+\s*[:.]?\s*)', '', phrase, flags=re.IGNORECASE).strip()
                cleaned_phrases.append(cleaned)
            content['phrases'] = cleaned_phrases
            content['evaluation_score'] = result.get('evaluation_score', 7)
            content['value_delivered'] = result.get('final_value_delivered', '')
            safe_print(f"   Score: {result.get('evaluation_score', 'N/A')}/10")
            if result.get('improvements_made'):
                safe_print(f"   Improvements: {result.get('improvements_made', [])[:2]}")
        
        return content
    
    # ========================================================================
    # STAGE 4: AI Generates B-Roll Keywords
    # ========================================================================
    def stage4_broll_keywords(self, phrases: List[str]) -> List[str]:
        """AI generates visual keywords for each phrase."""
        safe_print("\n[STAGE 4] AI generating visual keywords...")
        
        prompt = f"""You are a VISUAL DIRECTOR for viral short videos.
Select the PERFECT B-roll visual for EACH phrase.

=== PHRASES ===
{json.dumps(phrases, indent=2)}

=== VISUAL RULES ===
- Be SPECIFIC: "close up of person stressed at desk" > "stress"
- Match EMOTION to content
- Include PEOPLE when possible (more engaging)
- Think about MOVEMENT and COLOR

=== OUTPUT ===
Return exactly {len(phrases)} keywords as JSON array:
["specific keyword for phrase 1", "specific keyword for phrase 2", ...]

JSON ARRAY ONLY."""

        response = self.call_ai(prompt, 400, temperature=0.8)
        
        try:
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                keywords = json.loads(response[start:end])
                safe_print(f"   Generated {len(keywords)} visual keywords")
                return keywords[:len(phrases)]
        except:
            pass
        
        return ["dramatic scene"] * len(phrases)
    
    # ========================================================================
    # STAGE 5: AI Generates Metadata
    # ========================================================================
    def stage5_metadata(self, content: Dict) -> Dict:
        """AI generates viral metadata."""
        safe_print("\n[STAGE 5] AI generating metadata...")
        
        concept = content.get('concept', {})
        phrases = content.get('phrases', [])
        
        prompt = f"""Create viral metadata for this video.

Category: {concept.get('category', '')}
Topic: {concept.get('specific_topic', '')}
First phrase: {phrases[0] if phrases else ''}
Value: {content.get('value_delivered', '')}

=== OUTPUT JSON ===
{{
    "title": "viral title under 50 chars (include numbers if relevant)",
    "description": "2-3 sentence description with CTA",
    "hashtags": ["#shorts", "#viral", plus 5-8 relevant hashtags]
}}

JSON ONLY."""

        response = self.call_ai(prompt, 300, temperature=0.8)
        result = self.parse_json(response)
        
        if result:
            safe_print(f"   Title: {result.get('title', 'N/A')}")
        
        return result
    
    # ========================================================================
    # STAGE 6: Get Voice and Music with VARIETY ENFORCEMENT
    # ========================================================================
    def get_voice_config(self, concept: Dict, batch_tracker: BatchTracker = None) -> Dict:
        """AI-DRIVEN voice selection with variety enforcement."""
        category = concept.get('category', 'general')
        topic = concept.get('specific_topic', '')
        voice_style = concept.get('voice_style', 'energetic').lower()
        
        # Build exclusion list from batch tracker
        exclude_voices = []
        if batch_tracker and batch_tracker.used_voices:
            exclude_voices = batch_tracker.used_voices.copy()
        
        # AI selects the best voice for this content
        safe_print(f"   🎤 AI selecting voice for {category}/{voice_style}...")
        
        prompt = f"""You are a CASTING DIRECTOR for viral short videos.
Select the PERFECT narrator voice for this video.

=== VIDEO DETAILS ===
Category: {category}
Topic: {topic}
Desired Style: {voice_style}

=== AVAILABLE VOICES ===
{json.dumps(EDGE_TTS_VOICES, indent=2)}

=== VOICES TO AVOID (already used in this batch) ===
{json.dumps(exclude_voices) if exclude_voices else "None - all voices available"}

=== SELECTION CRITERIA ===
- Match voice CHARACTER to content (male/female, accent, energy)
- NEVER pick a voice from the "avoid" list
- Consider: US voices for general, AU/GB for variety, CA for friendly
- Female voices: Aria, Jenny, Michelle, Sara, Natasha, Sonia, Libby, Clara, Neerja
- Male voices: Guy, Davis, Christopher, Eric, Roger, Steffan, William, Ryan, Liam, Connor, Mitchell

=== OUTPUT JSON ===
{{"voice": "exact-voice-name-from-list", "rate": "+X%" or "-X%", "reasoning": "brief why"}}

JSON ONLY."""

        response = self.call_ai(prompt, 200, temperature=0.8)
        result = self.parse_json(response)
        
        if result and result.get('voice') in EDGE_TTS_VOICES:
            selected_voice = result['voice']
            rate = result.get('rate', '+0%')
            # Ensure not in exclusion list
            if selected_voice in exclude_voices:
                # AI ignored exclusion, pick random unused
                unused = [v for v in EDGE_TTS_VOICES if v not in exclude_voices]
                selected_voice = random.choice(unused) if unused else random.choice(EDGE_TTS_VOICES)
                rate = DEFAULT_VOICE_RATES.get(voice_style, '+0%')
            safe_print(f"   ✅ AI selected: {selected_voice}")
        else:
            # Fallback: random unused voice
            unused = [v for v in EDGE_TTS_VOICES if v not in exclude_voices]
            selected_voice = random.choice(unused) if unused else random.choice(EDGE_TTS_VOICES)
            rate = DEFAULT_VOICE_RATES.get(voice_style, '+0%')
            safe_print(f"   ⚠️ Fallback voice: {selected_voice}")
        
        # Track usage
        if batch_tracker:
            batch_tracker.used_voices.append(selected_voice)
        
        return {'voice': selected_voice, 'rate': rate}
    
    def get_music_path(self, concept: Dict, batch_tracker: BatchTracker = None) -> Optional[str]:
        """Get music path with variety enforcement."""
        music_mood = concept.get('music_mood', 'dramatic').lower()
        
        # Enforce variety: avoid recently used music
        available_moods = list(ALL_MUSIC.keys())
        if batch_tracker and batch_tracker.used_music:
            unused = [m for m in available_moods if ALL_MUSIC[m] not in batch_tracker.used_music[-3:]]
            if unused:
                # Prefer the AI-requested mood if available
                if music_mood in unused:
                    available_moods = [music_mood]
                else:
                    available_moods = unused
        
        selected_mood = music_mood if music_mood in available_moods else random.choice(available_moods)
        music_file = ALL_MUSIC.get(selected_mood, 'bensound-epic.mp3')
        
        # Track usage
        if batch_tracker:
            batch_tracker.used_music.append(music_file)
        
        return music_file


class VideoRenderer:
    """Professional video rendering."""
    
    def __init__(self):
        self.pexels_key = os.environ.get("PEXELS_API_KEY")
    
    def clean_phrase_prefix(self, phrase: str) -> str:
        """Removes 'Phrase X:' or similar prefixes from the start of a phrase."""
        # Regex to match "Phrase 1:", "Phrase 2.", "Phrase 3 -", etc.
        cleaned = re.sub(r'^(Phrase\s*\d+\s*[:.\-]?\s*)', '', phrase, flags=re.IGNORECASE).strip()
        return cleaned
    
    def download_broll(self, keyword: str, index: int) -> Optional[str]:
        """Download B-roll from Pexels."""
        if not self.pexels_key:
            return None
        
        safe_keyword = "".join(c if c.isalnum() or c == '_' else '_' for c in keyword)[:30]
        cache_file = BROLL_DIR / f"v7_{safe_keyword}_{index}_{random.randint(1000,9999)}.mp4"
        
        try:
            headers = {"Authorization": self.pexels_key}
            url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=10"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None
            
            videos = response.json().get("videos", [])
            if not videos:
                return None
            
            video = random.choice(videos)
            video_files = video.get("video_files", [])
            
            best = None
            for vf in video_files:
                if vf.get("quality") == "hd" and vf.get("height", 0) >= 720:
                    best = vf
                    break
            if not best and video_files:
                best = video_files[0]
            
            if not best:
                return None
            
            video_url = best.get("link")
            video_response = requests.get(video_url, timeout=60, stream=True)
            
            with open(cache_file, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            safe_print(f"   [OK] B-roll: {keyword[:25]}...")
            return str(cache_file)
            
        except Exception as e:
            return None
    
    def create_text_overlay(self, text: str, width: int, height: int) -> Image.Image:
        """Create text overlay."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        text = strip_emojis(text)
        
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/ariblk.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        font_path = next((f for f in font_paths if os.path.exists(f)), None)
        
        try:
            font = ImageFont.truetype(font_path, 64) if font_path else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        words = text.split()
        lines = []
        current = []
        max_width = width - 100
        
        for word in words:
            current.append(word)
            test = " ".join(current)
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width:
                current.pop()
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        
        line_height = 80
        total_height = len(lines) * line_height
        y = (height - total_height) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - (bbox[2] - bbox[0])) // 2
            
            for ox in range(-4, 5):
                for oy in range(-4, 5):
                    if ox != 0 or oy != 0:
                        draw.text((x + ox, y + oy), line, fill=(0, 0, 0, 255), font=font)
            
            draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
            y += line_height
        
        return img
    
    def create_progress_bar(self, duration: float) -> VideoClip:
        """Create progress bar."""
        bar_height = 6
        
        def make_frame(t):
            progress = t / duration
            frame = np.zeros((bar_height + 4, VIDEO_WIDTH, 3), dtype=np.uint8)
            frame[2:bar_height+2, :, :] = [40, 40, 40]
            fill_width = int(VIDEO_WIDTH * progress)
            if fill_width > 0:
                for x in range(fill_width):
                    ratio = x / max(fill_width, 1)
                    frame[2:bar_height+2, x, :] = [255, int(100 + 155 * ratio), 255]
            return frame
        
        return VideoClip(make_frame, duration=duration)
    
    def pil_to_clip(self, pil_img: Image.Image, duration: float) -> ImageClip:
        """Convert PIL RGBA to MoviePy clip with proper transparency."""
        rgba_arr = np.array(pil_img.convert('RGBA'))
        
        # Extract RGB and Alpha channels separately
        rgb_arr = rgba_arr[:, :, :3]
        alpha_arr = rgba_arr[:, :, 3] / 255.0  # Normalize alpha to 0-1
        
        # Create the main clip from RGB
        clip = ImageClip(rgb_arr, duration=duration)
        
        # Create mask from alpha channel
        mask_clip = ImageClip(alpha_arr, duration=duration, ismask=True)
        clip = clip.set_mask(mask_clip)
        
        return clip
    
    def create_animated_text_clip(self, text: str, duration: float, phrase_index: int = 0) -> VideoClip:
        """
        Create animated text overlay with professional effects.
        OPTIMIZED: Uses MoviePy built-in effects for speed.
        
        Effects cycle by phrase for variety.
        """
        width, height = VIDEO_WIDTH, VIDEO_HEIGHT // 2
        text_img = self.create_text_overlay(text, width, height)
        base_clip = self.pil_to_clip(text_img, duration)
        
        # Animation timing - quick fade in
        anim_duration = min(0.3, duration * 0.1)  # 10% of clip or 0.3s max
        
        # Choose effect based on phrase index for variety
        # All use efficient MoviePy built-in effects
        effect_type = phrase_index % 4
        
        if effect_type == 0:
            # Fade in (hook - simple but effective)
            return base_clip.set_position(('center', 'center')).crossfadein(anim_duration)
        
        elif effect_type == 1:
            # Slide in from left using set_position with lambda
            def position(t):
                if t < anim_duration:
                    progress = min(1.0, t / anim_duration)
                    ease = 1 - pow(1 - progress, 3)
                    x = int(-width/2 + (width/2 * ease))
                else:
                    x = 0
                return (x, 'center')
            return base_clip.set_position(position)
        
        elif effect_type == 2:
            # Slide in from right
            def position(t):
                if t < anim_duration:
                    progress = min(1.0, t / anim_duration)
                    ease = 1 - pow(1 - progress, 3)
                    x = int(width/2 - (width/2 * ease))
                else:
                    x = 0
                return (x, 'center')
            return base_clip.set_position(position)
        
        else:
            # Fade in (default - fastest)
            return base_clip.set_position(('center', 'center')).crossfadein(anim_duration)
    
    def get_sfx_for_phrase(self, phrase_index: int, total_phrases: int) -> Optional[str]:
        """
        Get appropriate sound effect for a phrase.
        
        - Hook (0): dramatic hit
        - Last phrase: ding (payoff)
        - Others: occasional whoosh for transitions
        """
        try:
            from sound_effects import get_all_sfx
            sfx = get_all_sfx()
            
            if phrase_index == 0:
                return sfx.get('hit')  # Dramatic hit for hook
            elif phrase_index == total_phrases - 1:
                return sfx.get('ding')  # Ding for payoff/CTA
            elif phrase_index % 2 == 1:
                return sfx.get('whoosh')  # Whoosh for some transitions
            return None
        except Exception as e:
            return None
    
    def create_vignette_overlay(self, width: int, height: int, intensity: float = 0.4) -> Image.Image:
        """
        Create a vignette overlay for cinematic effect.
        OPTIMIZED: Uses numpy vectorized operations (100x faster than per-pixel).
        """
        # Create coordinate grids
        y_coords, x_coords = np.ogrid[:height, :width]
        
        center_x, center_y = width // 2, height // 2
        max_distance = math.sqrt(center_x**2 + center_y**2)
        
        # Vectorized distance calculation
        distance = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        normalized = distance / max_distance
        
        # Apply intensity curve and convert to alpha
        alpha = (255 * intensity * (normalized ** 1.5)).astype(np.uint8)
        alpha = np.clip(alpha, 0, 255)
        
        # Create RGBA array
        vignette_array = np.zeros((height, width, 4), dtype=np.uint8)
        vignette_array[:, :, 3] = alpha  # Set alpha channel
        
        return Image.fromarray(vignette_array, 'RGBA')
    
    def apply_color_grade(self, clip: VideoClip, mood: str = 'dramatic') -> VideoClip:
        """
        Apply cinematic color grading based on mood.
        """
        # Color grade multipliers for different moods
        grades = {
            'dramatic': (1.0, 0.95, 1.1),      # Slightly blue, desaturated
            'energetic': (1.1, 1.0, 0.95),     # Warm, punchy
            'mysterious': (0.95, 0.95, 1.15),  # Cool blue
            'inspirational': (1.05, 1.05, 1.0), # Warm, uplifting
            'chill': (0.98, 1.02, 1.02),       # Cool, calm
            'emotional': (1.0, 0.92, 1.05),    # Desaturated, moody
            'tech': (0.95, 1.0, 1.1),          # Cool tech blue
            'default': (1.0, 1.0, 1.0),        # No change
        }
        
        r_mult, g_mult, b_mult = grades.get(mood, grades['default'])
        
        def apply_grade(frame):
            # Apply RGB multipliers (clip to valid range)
            graded = frame.astype(float)
            graded[:, :, 0] = np.clip(graded[:, :, 0] * r_mult, 0, 255)
            graded[:, :, 1] = np.clip(graded[:, :, 1] * g_mult, 0, 255)
            graded[:, :, 2] = np.clip(graded[:, :, 2] * b_mult, 0, 255)
            return graded.astype(np.uint8)
        
        return clip.fl_image(apply_grade)


def get_background_music_with_skip(music_mood: str, skip_seconds: float = 3.0,
                                   category: str = "", content_summary: str = "") -> Optional[Tuple[str, float]]:
    """
    Get AI-selected background music and skip the silent intro.
    
    Uses AI to analyze content and find the best matching music.
    """
    try:
        # Try AI-driven music selection first
        from ai_music_selector import get_ai_selected_music
        music_path = get_ai_selected_music(category, music_mood, content_summary)
        if music_path:
            safe_print(f"   [OK] AI-selected music: {music_mood} (skipping first {skip_seconds}s)")
            return (music_path, skip_seconds)
    except ImportError:
        pass  # Fall back to legacy
    except Exception as e:
        safe_print(f"   [!] AI music selection failed: {e}")
    
    # Fallback to legacy system
    try:
        from background_music import get_background_music
        music_path = get_background_music(music_mood)
        if music_path:
            safe_print(f"   [OK] Music: {music_mood} (skipping first {skip_seconds}s)")
            return (music_path, skip_seconds)
    except Exception as e:
        safe_print(f"   [!] Music lookup failed: {e}")
    return None


async def generate_voiceover(text: str, voice_config: Dict, output_path: str) -> float:
    """Generate voiceover."""
    voice = voice_config.get('voice', 'en-US-AriaNeural')
    rate = voice_config.get('rate', '+0%')
    
    safe_print(f"   [TTS] Voice: {voice} (rate: {rate})")
    
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch="+0Hz")
    await communicate.save(output_path)
    
    audio = AudioFileClip(output_path)
    duration = audio.duration
    audio.close()
    
    return duration


async def render_video(content: Dict, broll_paths: List[str], output_path: str, 
                       voice_config: Dict, music_file: str) -> bool:
    """Render the final video."""
    safe_print("\n[RENDER] Starting video render...")
    
    phrases = content.get('phrases', [])
    concept = content.get('concept', {})
    
    if not phrases:
        return False
    
    # Remove duplicates
    seen = set()
    unique_phrases = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            unique_phrases.append(p)
    phrases = unique_phrases
    
    safe_print(f"   Phrases: {len(phrases)}")
    
    # Generate voiceover
    full_text = ". ".join(phrases)
    voiceover_path = str(CACHE_DIR / f"vo_{random.randint(1000,9999)}.mp3")
    
    try:
        duration = await generate_voiceover(full_text, voice_config, voiceover_path)
        safe_print(f"   [OK] Voiceover: {duration:.1f}s")
    except Exception as e:
        safe_print(f"   [!] Voiceover failed: {e}")
        return False
    
    # Calculate timings
    total_chars = sum(len(p) for p in phrases)
    phrase_durations = []
    for phrase in phrases:
        char_ratio = len(phrase) / total_chars
        phrase_dur = char_ratio * duration
        phrase_dur = max(phrase_dur, 2.0)
        phrase_durations.append(phrase_dur)
    
    total_calc = sum(phrase_durations)
    if total_calc > 0:
        scale = duration / total_calc
        phrase_durations = [d * scale for d in phrase_durations]
    
    safe_print(f"   Timings: {[f'{d:.1f}s' for d in phrase_durations]}")
    
    while len(broll_paths) < len(phrases):
        broll_paths.append(None)
    
    # Get AI-selected music with intro skip
    # Pass content context for better AI selection
    category = concept.get('category', 'general')
    content_summary = phrases[0] if phrases else ''  # Use hook as summary
    music_result = get_background_music_with_skip(
        music_file, 
        skip_seconds=3.0,
        category=category,
        content_summary=content_summary
    )
    
    # Create segments
    renderer = VideoRenderer()
    segments = []
    
    for i, (phrase, broll_path, dur) in enumerate(zip(phrases, broll_paths, phrase_durations)):
        safe_print(f"   [*] Segment {i+1}/{len(phrases)}")
        
        layers = []
        
        if broll_path and os.path.exists(broll_path):
            try:
                bg = VideoFileClip(broll_path)
                
                bg_ratio = bg.size[0] / bg.size[1]
                target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
                
                if bg_ratio > target_ratio:
                    new_height = VIDEO_HEIGHT
                    new_width = int(new_height * bg_ratio)
                else:
                    new_width = VIDEO_WIDTH
                    new_height = int(new_width / bg_ratio)
                
                bg = bg.resize((new_width, new_height))
                
                x_offset = (new_width - VIDEO_WIDTH) // 2
                y_offset = (new_height - VIDEO_HEIGHT) // 2
                bg = bg.crop(x1=x_offset, y1=y_offset, x2=x_offset+VIDEO_WIDTH, y2=y_offset+VIDEO_HEIGHT)
                
                if bg.duration < dur:
                    bg = bg.loop(duration=dur)
                bg = bg.subclip(0, dur)
                
                # Apply cinematic effects
                bg = bg.fx(vfx.colorx, 0.6)  # Slight darken for text readability
                
                # Apply color grading based on music mood
                try:
                    bg = renderer.apply_color_grade(bg, music_file)
                except:
                    pass  # Skip if color grading fails
                
                layers.append(bg)
                
                # Add vignette overlay for cinematic look
                try:
                    vignette_img = renderer.create_vignette_overlay(VIDEO_WIDTH, VIDEO_HEIGHT, intensity=0.3)
                    vignette_clip = renderer.pil_to_clip(vignette_img, dur)
                    layers.append(vignette_clip)
                except:
                    pass  # Skip if vignette fails
                    
            except Exception as e:
                broll_path = None
        
        if not broll_path or not layers:
            # Dynamic gradient based on content category
            gradient = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
            colors = [(30 + i*10, 20 + i*5, 50 + i*8), (60 + i*15, 40 + i*10, 90 + i*12)]
            for y in range(VIDEO_HEIGHT):
                ratio = y / VIDEO_HEIGHT
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
                for x in range(VIDEO_WIDTH):
                    gradient.putpixel((x, y), (r, g, b))
            
            bg = renderer.pil_to_clip(gradient, dur)
            layers.append(bg)
        
        # Use animated text instead of static (clean any "Phrase X:" prefixes)
        clean_phrase = renderer.clean_phrase_prefix(phrase)
        text_clip = renderer.create_animated_text_clip(clean_phrase, dur, phrase_index=i)
        layers.append(text_clip)
        
        segment = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        segment = segment.set_duration(dur)
        segments.append(segment)
    
    safe_print("   [*] Concatenating segments...")
    final_video = concatenate_videoclips(segments, method="compose")
    
    progress_clip = renderer.create_progress_bar(final_video.duration)
    progress_clip = progress_clip.set_position(("center", 12))
    
    final_video = CompositeVideoClip(
        [final_video, progress_clip],
        size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    ).set_duration(final_video.duration)
    
    # Audio mixing - skip music intro + add sound effects
    vo_clip = AudioFileClip(voiceover_path)
    audio_layers = [vo_clip]
    
    # Add sound effects at phrase transitions
    try:
        sfx_clips = []
        cumulative_time = 0
        for i, dur in enumerate(phrase_durations):
            sfx_path = renderer.get_sfx_for_phrase(i, len(phrases))
            if sfx_path and os.path.exists(sfx_path):
                sfx = AudioFileClip(sfx_path).volumex(0.4)  # 40% volume
                # Position SFX at start of each phrase
                sfx = sfx.set_start(cumulative_time)
                sfx_clips.append(sfx)
            cumulative_time += dur
        if sfx_clips:
            audio_layers.extend(sfx_clips)
            safe_print(f"   [OK] Added {len(sfx_clips)} sound effects")
    except Exception as e:
        safe_print(f"   [!] SFX error (continuing without): {e}")
    
    # Add background music
    if music_result:
        music_path, skip_seconds = music_result
        try:
            music_clip = AudioFileClip(music_path)
            
            # Skip the silent intro
            if music_clip.duration > skip_seconds + final_video.duration:
                music_clip = music_clip.subclip(skip_seconds)
            
            music_clip = music_clip.volumex(0.15)
            
            if music_clip.duration < final_video.duration:
                music_clip = music_clip.loop(duration=final_video.duration)
            music_clip = music_clip.subclip(0, final_video.duration)
            
            audio_layers.append(music_clip)
        except Exception as e:
            safe_print(f"   [!] Music error: {e}")
    
    final_audio = CompositeAudioClip(audio_layers)
    
    final_video = final_video.set_audio(final_audio)
    
    safe_print("   [*] Rendering final video...")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        bitrate='8M',
        threads=4,
        logger=None
    )
    
    final_video.close()
    vo_clip.close()
    
    safe_print(f"   [OK] Created: {output_path}")
    return True


async def generate_pro_video(hint: str = None, batch_tracker: BatchTracker = None) -> Optional[str]:
    """
    Generate a video with 100% AI-driven decisions.
    VARIETY ENFORCED through batch_tracker.
    """
    run_id = random.randint(10000, 99999)
    
    safe_print("=" * 70)
    safe_print(f"   VIRALSHORTS FACTORY v7.1 - 100% AI-DRIVEN + VARIETY ENFORCED")
    safe_print(f"   Run: #{run_id}")
    safe_print("=" * 70)
    
    ai = MasterAI()
    if not ai.client and not ai.gemini_model:
        safe_print("[!] No AI available")
        return None
    
    # Stage 1: AI decides concept (with variety enforcement)
    concept = ai.stage1_decide_video_concept(hint, batch_tracker)
    if not concept:
        safe_print("[!] Concept generation failed")
        return None
    
    # Stage 2: AI creates content
    content = ai.stage2_create_content(concept)
    if not content or not content.get('phrases'):
        safe_print("[!] Content creation failed")
        return None
    
    # Stage 3: AI evaluates and enhances
    content = ai.stage3_evaluate_enhance(content)
    
    # Stage 4: AI generates B-roll keywords
    broll_keywords = ai.stage4_broll_keywords(content.get('phrases', []))
    
    # Stage 5: AI generates metadata
    metadata = ai.stage5_metadata(content)
    
    # Get voice and music with variety enforcement
    voice_config = ai.get_voice_config(concept, batch_tracker)
    music_file = ai.get_music_path(concept, batch_tracker)
    
    # Download B-roll
    safe_print("\n[BROLL] Downloading visuals...")
    renderer = VideoRenderer()
    broll_paths = []
    for i, keyword in enumerate(broll_keywords):
        path = renderer.download_broll(keyword, i)
        broll_paths.append(path)
    
    # Render
    category = concept.get('category', 'fact')
    safe_cat = "".join(c if c.isalnum() else '_' for c in category)[:20]
    output_path = str(OUTPUT_DIR / f"pro_{safe_cat}_{run_id}.mp4")
    
    success = await render_video(content, broll_paths, output_path, voice_config, music_file)
    
    if success:
        # Save metadata
        meta_path = output_path.replace('.mp4', '_meta.json')
        full_metadata = {
            'concept': concept,
            'content': content,
            'metadata': metadata,
            'broll_keywords': broll_keywords,
            'voice_config': voice_config,
            'music_file': music_file,
            'run_id': run_id
        }
        with open(meta_path, 'w') as f:
            json.dump(full_metadata, f, indent=2)
        
        # Track in batch with score
        score = content.get('evaluation_score', 7)
        if batch_tracker:
            batch_tracker.add_video(output_path, score, metadata or {})
        
        safe_print("\n" + "=" * 70)
        safe_print("   VIDEO GENERATED!")
        safe_print(f"   File: {output_path}")
        safe_print(f"   Category: {concept.get('category', 'N/A')}")
        safe_print(f"   Topic: {concept.get('specific_topic', 'N/A')}")
        safe_print(f"   Voice: {voice_config.get('voice', 'N/A')}")
        safe_print(f"   Music: {music_file}")
        safe_print(f"   Score: {score}/10")
        if metadata:
            safe_print(f"   Title: {metadata.get('title', 'N/A')}")
        safe_print("=" * 70)
        
        return output_path
    
    return None


async def upload_video(video_path: str, metadata: Dict, youtube: bool = True, dailymotion: bool = True) -> Dict:
    """Upload to platforms."""
    results = {"youtube": None, "dailymotion": None}
    
    title = metadata.get('title', 'Amazing Fact')[:100]
    description = metadata.get('description', 'Follow for more!')[:5000]
    hashtags = metadata.get('hashtags', ['#shorts', '#viral'])
    tags = [h.replace('#', '').strip() for h in hashtags if h]
    
    safe_print(f"\n[UPLOAD] Title: {title}")
    
    if youtube:
        try:
            from youtube_uploader import upload_video as yt_upload
            result = yt_upload(video_path, title=title, description=description, tags=tags)
            if result:
                results["youtube"] = result
                safe_print(f"[OK] YouTube: {result}")
        except Exception as e:
            safe_print(f"[!] YouTube error: {e}")
    
    if dailymotion:
        try:
            from dailymotion_uploader import DailymotionUploader
            dm = DailymotionUploader()
            if dm.is_configured:
                result = dm.upload_video(
                    video_path, title=title, description=description,
                    tags=tags, channel='lifestyle', ai_generated=False
                )
                if result:
                    results["dailymotion"] = result
                    safe_print(f"[OK] Dailymotion: {result}")
        except Exception as e:
            safe_print(f"[!] Dailymotion error: {e}")
    
    return results


async def main():
    """Generate videos with 100% AI decision-making and VARIETY ENFORCEMENT."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--hint", default=None, help="Optional hint for AI")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--strategic-youtube", action="store_true", 
                        help="Upload BEST video to YouTube, all to Dailymotion")
    # Legacy support - these are IGNORED, AI decides
    parser.add_argument("--type", default=None, help="IGNORED - AI decides type")
    args = parser.parse_args()
    
    should_upload = args.upload and not args.no_upload
    
    safe_print(f"\n{'='*70}")
    safe_print("   VIRALSHORTS FACTORY v7.1 - 100% AI-DRIVEN + VARIETY ENFORCED")
    safe_print(f"   Generating {args.count} video(s)")
    safe_print("   AI decides: category, topic, length, voice, music")
    safe_print("   VARIETY ENFORCED: Each video will be DIFFERENT!")
    if args.strategic_youtube:
        safe_print("   STRATEGIC YOUTUBE: Best video selected by score")
    safe_print(f"{'='*70}")
    
    # Reset batch tracker for new batch
    global BATCH_TRACKER
    BATCH_TRACKER = BatchTracker()
    
    hint = args.hint or args.type
    
    for i in range(args.count):
        safe_print(f"\n{'='*70}")
        safe_print(f"   VIDEO {i+1}/{args.count}")
        safe_print(f"{'='*70}")
        
        path = await generate_pro_video(hint, BATCH_TRACKER)
    
    # Upload phase
    if should_upload and BATCH_TRACKER.video_scores:
        safe_print("\n" + "=" * 70)
        safe_print("   UPLOADING")
        safe_print("=" * 70)
        
        if args.strategic_youtube:
            # Strategic: Best video to YouTube, all to Dailymotion
            best = BATCH_TRACKER.get_best_video_for_youtube()
            if best:
                best_path, best_meta = best
                safe_print(f"\n[YOUTUBE] Uploading BEST video (score-based selection)")
                await upload_video(best_path, best_meta, youtube=True, dailymotion=True)
                # IMPORTANT: Wait after first upload before starting Dailymotion batch
                initial_delay = random.randint(120, 180)  # 2-3 minutes after first
                safe_print(f"[WAIT] Initial cooldown: {initial_delay}s before Dailymotion batch")
                time.sleep(initial_delay)
            
            # All other videos to Dailymotion only (SEQUENTIAL with longer delays)
            remaining_videos = [(p, m) for p, m in BATCH_TRACKER.get_all_videos() 
                               if not best or p != best[0]]
            
            for idx, (video_path, metadata) in enumerate(remaining_videos):
                safe_print(f"\n[DAILYMOTION ONLY] ({idx+1}/{len(remaining_videos)}) {video_path}")
                await upload_video(video_path, metadata, youtube=False, dailymotion=True)
                
                # Skip delay after last video
                if idx < len(remaining_videos) - 1:
                    # Longer delays to prevent Dailymotion 403 rate limiting
                    delay = random.randint(150, 240)  # 2.5-4 minutes between uploads
                    safe_print(f"[WAIT] Anti-ban delay: {delay}s (prevents 403 errors)")
                    time.sleep(delay)
        else:
            # Legacy: Upload all to both platforms
            for video_path, metadata in BATCH_TRACKER.get_all_videos():
                await upload_video(video_path, metadata)
                if len(BATCH_TRACKER.video_scores) > 1:
                    delay = random.randint(45, 120)
                    safe_print(f"[WAIT] Anti-ban delay: {delay}s")
                    time.sleep(delay)
    
    # Print summary
    safe_print(f"\n{'='*70}")
    safe_print(f"   COMPLETE: {len(BATCH_TRACKER.video_scores)} videos")
    safe_print(f"{'='*70}")
    
    # Print the table of all videos
    safe_print("\n=== VIDEO DETAILS TABLE ===")
    safe_print("-" * 100)
    safe_print(f"{'#':>2} | {'Category':<15} | {'Topic':<25} | {'Voice':<20} | {'Music':<20} | {'Score':>5}")
    safe_print("-" * 100)
    
    for i, (path, score, meta) in enumerate(BATCH_TRACKER.video_scores, 1):
        # Load full metadata from file
        meta_path = path.replace('.mp4', '_meta.json')
        full_meta = {}
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                full_meta = json.load(f)
        
        concept = full_meta.get('concept', {})
        voice_config = full_meta.get('voice_config', {})
        
        category = concept.get('category', 'N/A')[:15]
        topic = concept.get('specific_topic', 'N/A')[:25]
        voice = voice_config.get('voice', 'N/A').split('-')[-1].replace('Neural', '')[:20]
        music = full_meta.get('music_file', 'N/A')[:20]
        
        safe_print(f"{i:>2} | {category:<15} | {topic:<25} | {voice:<20} | {music:<20} | {score:>5}/10")
    
    safe_print("-" * 100)


if __name__ == "__main__":
    asyncio.run(main())

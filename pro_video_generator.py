#!/usr/bin/env python3
"""
ViralShorts Factory - PROFESSIONAL Video Generator v6.0
========================================================

MAJOR IMPROVEMENTS:
1. 6 Video Types with Weighting System (analytics-driven)
2. Longer videos (30-45 seconds) with more value
3. GLOBAL focus (not US-only)
4. Music plays from START (fixed)
5. Multi-stage AI for maximum quality
6. Analytics feedback integration for type weighting

VIDEO TYPES (6 categories):
1. psychology_fact - Mind-blowing psychology insights
2. money_fact - Financial wisdom (global)
3. life_hack - Practical life tips
4. statistics_fact - Surprising statistics
5. science_fact - Amazing science facts
6. motivation - Inspiring/motivational content
"""

import os
import sys
import re
import json
import asyncio
import random
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
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
# Fix Pillow 10+ compatibility - ANTIALIAS was removed
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import edge_tts

# Constants
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BROLL_DIR = Path("./assets/broll")
BROLL_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
WEIGHTS_FILE = Path("./type_weights.json")


def safe_print(msg: str):
    """Print with fallback for Windows encoding issues."""
    try:
        print(msg)
    except UnicodeEncodeError:
        clean = re.sub(r'[^\x00-\x7F]+', '', msg)
        print(clean)


def strip_emojis(text: str) -> str:
    """Remove emojis to prevent rendering issues."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()


# ============================================================================
# 6 VIDEO TYPES WITH CONFIGURATIONS
# ============================================================================

VIDEO_TYPES = {
    "psychology_fact": {
        "name": "Psychology Fact",
        "voice": "en-US-AriaNeural",
        "rate": "+5%",
        "music_mood": "mystery",
        "gradient": [(40, 20, 60), (80, 40, 100)],
        "description": "Mind-blowing psychology insights that change behavior",
    },
    "money_fact": {
        "name": "Money Fact", 
        "voice": "en-US-GuyNeural",
        "rate": "+8%",
        "music_mood": "energetic",
        "gradient": [(20, 50, 30), (40, 100, 60)],
        "description": "Financial wisdom applicable GLOBALLY (not US-only)",
    },
    "life_hack": {
        "name": "Life Hack",
        "voice": "en-US-JennyNeural",
        "rate": "+10%",
        "music_mood": "fun",
        "gradient": [(60, 60, 20), (100, 100, 40)],
        "description": "Practical life tips anyone can use immediately",
    },
    "statistics_fact": {
        "name": "Statistics Fact",
        "voice": "en-US-DavisNeural",
        "rate": "+5%",
        "music_mood": "mystery",
        "gradient": [(30, 40, 60), (60, 80, 120)],
        "description": "Surprising statistics that shock and educate",
    },
    "science_fact": {
        "name": "Science Fact",
        "voice": "en-US-ChristopherNeural",
        "rate": "+3%",
        "music_mood": "dramatic",
        "gradient": [(20, 30, 50), (50, 70, 110)],
        "description": "Amazing science facts that blow minds",
    },
    "motivation": {
        "name": "Motivation",
        "voice": "en-US-AriaNeural",
        "rate": "+0%",
        "music_mood": "energetic",
        "gradient": [(50, 30, 20), (100, 60, 40)],
        "description": "Inspiring content that motivates action",
    },
}


class TypeWeightManager:
    """
    Manages weights for video types based on analytics performance.
    Starts with equal weights (1/6), adjusts based on views/engagement.
    """
    
    def __init__(self):
        self.weights = self._load_weights()
    
    def _load_weights(self) -> Dict[str, float]:
        """Load weights from file or create default."""
        if WEIGHTS_FILE.exists():
            try:
                with open(WEIGHTS_FILE) as f:
                    return json.load(f)
            except:
                pass
        
        # Default: equal weights
        types = list(VIDEO_TYPES.keys())
        return {t: 1.0 / len(types) for t in types}
    
    def save_weights(self):
        """Save weights to file."""
        with open(WEIGHTS_FILE, 'w') as f:
            json.dump(self.weights, f, indent=2)
    
    def get_weighted_type(self) -> str:
        """Select a video type based on weights."""
        types = list(self.weights.keys())
        weights = list(self.weights.values())
        return random.choices(types, weights=weights, k=1)[0]
    
    def update_from_analytics(self, analytics_data: Dict):
        """
        Update weights based on analytics performance.
        Higher views/engagement = higher weight.
        """
        if not analytics_data:
            return
        
        # Calculate performance scores per type
        type_scores = {}
        for video_type in VIDEO_TYPES:
            type_videos = [v for v in analytics_data if v.get('type') == video_type]
            if type_videos:
                avg_views = sum(v.get('views', 0) for v in type_videos) / len(type_videos)
                avg_engagement = sum(v.get('engagement', 0) for v in type_videos) / len(type_videos)
                type_scores[video_type] = avg_views + (avg_engagement * 10)
            else:
                type_scores[video_type] = 1  # Minimum score
        
        # Normalize to weights
        total = sum(type_scores.values())
        if total > 0:
            self.weights = {t: max(0.05, s / total) for t, s in type_scores.items()}
            self.save_weights()
            safe_print(f"[WEIGHTS] Updated: {self.weights}")


class MultiStageAI:
    """
    Multi-stage AI content generation with chained prompts.
    FRESH generation for EACH video!
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
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                safe_print("[OK] Gemini AI initialized")
            except Exception as e:
                safe_print(f"[!] Gemini init failed: {e}")
    
    def call_ai(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.9) -> str:
        """Call AI with automatic fallback."""
        # Try Groq
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
        
        # Fallback to Gemini
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
    
    def generate_content(self, video_type: str, run_id: int) -> Dict:
        """
        Generate viral content with 6 phrases for 30-45 second videos.
        GLOBAL focus - not country-specific.
        """
        safe_print(f"\n[AI] Generating {video_type} content (run #{run_id})...")
        
        type_config = VIDEO_TYPES.get(video_type, VIDEO_TYPES["psychology_fact"])
        unique_seed = f"{video_type}_{run_id}_{time.time()}"
        
        prompt = f"""You are a VIRAL CONTENT MASTERMIND creating SHORT-FORM video content.
Your videos get MILLIONS of views because you deliver REAL, ACTIONABLE value.

=== GENERATION PARAMETERS ===
UNIQUE ID: {unique_seed}
TYPE: {video_type} - {type_config['description']}
DATE: {time.strftime('%B %d, %Y')}

=== CRITICAL REQUIREMENTS ===

1. **GLOBAL FOCUS**: Content must be relevant WORLDWIDE, not specific to any country.
   - BAD: "In the US, taxes work like..."
   - GOOD: "Globally, 73% of people..."
   
2. **LONGER FORMAT (30-45 seconds)**: Create 6 phrases that build a complete story:
   - Phrase 1: HOOK (pattern interrupt, curiosity gap)
   - Phrase 2: PROBLEM (relatable pain point)
   - Phrase 3: CONTEXT (why this matters)
   - Phrase 4: SOLUTION PART 1 (the technique/method)
   - Phrase 5: SOLUTION PART 2 (how to apply it)
   - Phrase 6: PAYOFF (transformation/result + subtle CTA)

3. **REAL VALUE**: Every phrase must add information. No fluff!
   - Include SPECIFIC numbers, percentages, timeframes
   - Include ACTIONABLE steps viewers can take TODAY
   
4. **FORMAT**: 
   - Use DIGITS for numbers (500$, 92%, 3x)
   - Each phrase: 10-18 words
   - Total: ~90-110 words for 30-45 second video

=== OUTPUT JSON ===
{{
    "topic": "5-word topic description",
    "phrases": [
        "Phrase 1: Hook (10-15 words)",
        "Phrase 2: Problem (12-18 words)",
        "Phrase 3: Context (12-18 words)",
        "Phrase 4: Solution Part 1 (12-18 words)",
        "Phrase 5: Solution Part 2 (12-18 words)",
        "Phrase 6: Payoff (10-15 words)"
    ],
    "value_delivered": "What specific action can viewer take?",
    "global_relevance": "Why this works worldwide"
}}

OUTPUT JSON ONLY. Make this UNIQUE and VALUABLE!"""

        response = self.call_ai(prompt, 1500, temperature=0.95)
        result = self.parse_json(response)
        
        if result and result.get('phrases'):
            result['video_type'] = video_type
            result['run_id'] = run_id
            safe_print(f"   Topic: {result.get('topic', 'N/A')}")
            safe_print(f"   Phrases: {len(result.get('phrases', []))}")
            safe_print(f"   Value: {result.get('value_delivered', 'N/A')}")
        
        return result
    
    def enhance_content(self, content: Dict) -> Dict:
        """Stage 2: Validate and enhance content quality."""
        safe_print("\n[AI] Enhancing content...")
        
        if not content or not content.get('phrases'):
            return content
        
        prompt = f"""You are a VIRAL CONTENT OPTIMIZER.
Improve this content for MAXIMUM engagement and value.

=== ORIGINAL CONTENT ===
{json.dumps(content.get('phrases', []), indent=2)}

=== YOUR TASKS ===
1. Ensure GLOBAL relevance (no country-specific content)
2. Verify each phrase adds VALUE (not fluff)
3. Check numbers are DIGITS (500$, 92%)
4. Ensure phrases build on each other
5. Make hook IRRESISTIBLE

=== OUTPUT JSON ===
{{
    "phrases": ["improved phrase 1", "improved phrase 2", ...],
    "value_score": 1-10,
    "improvements": ["what you improved"]
}}

JSON ONLY."""

        response = self.call_ai(prompt, 800, temperature=0.7)
        result = self.parse_json(response)
        
        if result and result.get('phrases'):
            content['phrases'] = result['phrases']
            content['value_score'] = result.get('value_score', 7)
            safe_print(f"   Value Score: {result.get('value_score', 'N/A')}/10")
        
        return content
    
    def generate_broll_keywords(self, phrases: List[str]) -> List[str]:
        """Generate B-roll keywords for each phrase."""
        safe_print("\n[AI] Generating B-roll keywords...")
        
        prompt = f"""Select the PERFECT B-roll visual for EACH phrase.

=== PHRASES ===
{json.dumps(phrases, indent=2)}

=== RULES ===
- Be SPECIFIC: "person holding phone in dark room" > "technology"
- Include EMOTION: tense visuals for problems, bright for solutions
- Match the CONTENT meaning

=== OUTPUT ===
Return exactly {len(phrases)} keywords as JSON array:
["keyword 1", "keyword 2", ...]

JSON ARRAY ONLY."""

        response = self.call_ai(prompt, 400, temperature=0.8)
        
        try:
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                keywords = json.loads(response[start:end])
                safe_print(f"   Keywords: {len(keywords)}")
                return keywords[:len(phrases)]
        except:
            pass
        
        # Fallback
        return ["dramatic scene"] * len(phrases)
    
    def generate_metadata(self, content: Dict) -> Dict:
        """Generate viral title, description, hashtags."""
        safe_print("\n[AI] Generating metadata...")
        
        prompt = f"""Create viral metadata for this content.

Topic: {content.get('topic', '')}
Type: {content.get('video_type', 'fact')}
First phrase: {content.get('phrases', [''])[0]}

=== OUTPUT JSON ===
{{
    "title": "viral title under 50 chars (include numbers if possible)",
    "description": "2-3 sentence description with global appeal",
    "hashtags": ["#shorts", "#viral", "#facts", "#mindblown", "#fyp", "#trending"]
}}

JSON ONLY."""

        response = self.call_ai(prompt, 300, temperature=0.8)
        result = self.parse_json(response)
        
        if result:
            safe_print(f"   Title: {result.get('title', 'N/A')}")
        
        return result


class ProVideoRenderer:
    """Professional video rendering with all enhancements."""
    
    def __init__(self):
        self.pexels_key = os.environ.get("PEXELS_API_KEY")
        safe_print(f"[OK] Pexels: {'configured' if self.pexels_key else 'MISSING'}")
    
    def download_broll(self, keyword: str, index: int) -> Optional[str]:
        """Download B-roll from Pexels."""
        if not self.pexels_key:
            return None
        
        safe_keyword = "".join(c if c.isalnum() or c == '_' else '_' for c in keyword)[:30]
        cache_file = BROLL_DIR / f"v6_{safe_keyword}_{index}_{random.randint(1000,9999)}.mp4"
        
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
            safe_print(f"   [!] B-roll error: {e}")
            return None
    
    def create_text_overlay(self, text: str, width: int, height: int) -> Image.Image:
        """Create professional text overlay."""
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
        """Create animated progress bar."""
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
        """Convert PIL Image to MoviePy ImageClip."""
        arr = np.array(pil_img.convert('RGBA'))
        return ImageClip(arr, duration=duration, ismask=False)


async def generate_voiceover(text: str, video_type: str, output_path: str) -> float:
    """Generate voiceover using Edge TTS with type-specific voice."""
    config = VIDEO_TYPES.get(video_type, VIDEO_TYPES["psychology_fact"])
    voice = config.get("voice", "en-US-AriaNeural")
    rate = config.get("rate", "+0%")
    
    safe_print(f"   [TTS] Voice: {voice} (rate: {rate})")
    
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch="+0Hz")
    await communicate.save(output_path)
    
    audio = AudioFileClip(output_path)
    duration = audio.duration
    audio.close()
    
    return duration


async def render_video(content: Dict, broll_paths: List[str], video_type: str, output_path: str) -> bool:
    """Render the final video with all enhancements."""
    safe_print("\n[RENDER] Starting video render...")
    
    phrases = content.get('phrases', [])
    if not phrases:
        safe_print("[!] No phrases")
        return False
    
    # Remove duplicates while preserving order
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
        duration = await generate_voiceover(full_text, video_type, voiceover_path)
        safe_print(f"   [OK] Voiceover: {duration:.1f}s")
    except Exception as e:
        safe_print(f"   [!] Voiceover failed: {e}")
        return False
    
    # Calculate phrase timings
    total_chars = sum(len(p) for p in phrases)
    phrase_durations = []
    for phrase in phrases:
        char_ratio = len(phrase) / total_chars
        phrase_dur = char_ratio * duration
        phrase_dur = max(phrase_dur, 2.0)
        phrase_durations.append(phrase_dur)
    
    # Scale to exact duration
    total_calc = sum(phrase_durations)
    if total_calc > 0:
        scale = duration / total_calc
        phrase_durations = [d * scale for d in phrase_durations]
    
    safe_print(f"   Timings: {[f'{d:.1f}s' for d in phrase_durations]}")
    
    # Ensure B-roll for every phrase
    while len(broll_paths) < len(phrases):
        broll_paths.append(None)
    
    # Get background music FIRST (before video segments)
    music_path = None
    music_mood = VIDEO_TYPES.get(video_type, {}).get("music_mood", "fun")
    try:
        from background_music import get_background_music
        music_path = get_background_music(music_mood)
        if music_path:
            safe_print(f"   [OK] Music: {music_mood}")
    except Exception as e:
        safe_print(f"   [!] Music error: {e}")
    
    # Create video segments
    renderer = ProVideoRenderer()
    segments = []
    type_config = VIDEO_TYPES.get(video_type, VIDEO_TYPES["psychology_fact"])
    
    for i, (phrase, broll_path, dur) in enumerate(zip(phrases, broll_paths, phrase_durations)):
        safe_print(f"   [*] Segment {i+1}/{len(phrases)}")
        
        layers = []
        
        # Background
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
                bg = bg.fx(vfx.colorx, 0.5)
                
                layers.append(bg)
            except Exception as e:
                safe_print(f"   [!] B-roll error: {e}")
                broll_path = None
        
        if not broll_path or not layers:
            colors = type_config.get("gradient", [(40, 40, 60), (80, 80, 100)])
            gradient = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
            for y in range(VIDEO_HEIGHT):
                ratio = y / VIDEO_HEIGHT
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
                for x in range(VIDEO_WIDTH):
                    gradient.putpixel((x, y), (r, g, b))
            
            bg = renderer.pil_to_clip(gradient, dur)
            layers.append(bg)
        
        # Text overlay
        text_img = renderer.create_text_overlay(phrase, VIDEO_WIDTH, VIDEO_HEIGHT // 2)
        text_clip = renderer.pil_to_clip(text_img, dur)
        text_clip = text_clip.set_position(('center', 'center'))
        layers.append(text_clip)
        
        segment = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        segment = segment.set_duration(dur)
        segments.append(segment)
    
    # Concatenate
    safe_print("   [*] Concatenating segments...")
    final_video = concatenate_videoclips(segments, method="compose")
    
    # Add progress bar
    progress_clip = renderer.create_progress_bar(final_video.duration)
    progress_clip = progress_clip.set_position(("center", 12))
    
    final_video = CompositeVideoClip(
        [final_video, progress_clip],
        size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    ).set_duration(final_video.duration)
    
    # Add audio - MUSIC FROM START
    vo_clip = AudioFileClip(voiceover_path)
    
    if music_path and os.path.exists(music_path):
        try:
            music_clip = AudioFileClip(music_path)
            # Set consistent volume from start
            music_clip = music_clip.volumex(0.15)
            
            if music_clip.duration < final_video.duration:
                music_clip = music_clip.loop(duration=final_video.duration)
            music_clip = music_clip.subclip(0, final_video.duration)
            
            # Mix voiceover and music - both start at 0
            final_audio = CompositeAudioClip([vo_clip, music_clip])
        except Exception as e:
            safe_print(f"   [!] Music mix error: {e}")
            final_audio = vo_clip
    else:
        final_audio = vo_clip
    
    final_video = final_video.set_audio(final_audio)
    
    # Render
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
    
    # Cleanup
    final_video.close()
    vo_clip.close()
    
    safe_print(f"   [OK] Created: {output_path}")
    return True


async def generate_pro_video(video_type: str = None, run_id: int = None) -> Optional[str]:
    """Generate a professional video using multi-stage AI."""
    if run_id is None:
        run_id = random.randint(10000, 99999)
    
    # Use weight manager for type selection if not specified
    if video_type is None:
        weight_manager = TypeWeightManager()
        video_type = weight_manager.get_weighted_type()
    
    safe_print("=" * 70)
    safe_print(f"   PROFESSIONAL VIDEO GENERATOR v6.0")
    safe_print(f"   Type: {video_type} | Run: #{run_id}")
    safe_print("=" * 70)
    
    # Initialize AI
    ai = MultiStageAI()
    if not ai.client and not ai.gemini_model:
        safe_print("[!] No AI available")
        return None
    
    # Stage 1: Generate content
    content = ai.generate_content(video_type, run_id)
    if not content or not content.get('phrases'):
        safe_print("[!] Content generation failed")
        return None
    
    # Stage 2: Enhance content
    content = ai.enhance_content(content)
    
    # Stage 3: B-roll keywords
    broll_keywords = ai.generate_broll_keywords(content.get('phrases', []))
    
    # Stage 4: Metadata
    metadata = ai.generate_metadata(content)
    
    # Download B-roll
    safe_print("\n[BROLL] Downloading visuals...")
    renderer = ProVideoRenderer()
    broll_paths = []
    for i, keyword in enumerate(broll_keywords):
        path = renderer.download_broll(keyword, i)
        broll_paths.append(path)
    
    # Render video
    output_path = str(OUTPUT_DIR / f"pro_{video_type}_{run_id}.mp4")
    
    success = await render_video(content, broll_paths, video_type, output_path)
    
    if success:
        # Save metadata
        meta_path = output_path.replace('.mp4', '_meta.json')
        with open(meta_path, 'w') as f:
            json.dump({
                'content': content,
                'metadata': metadata,
                'broll_keywords': broll_keywords,
                'video_type': video_type,
                'run_id': run_id
            }, f, indent=2)
        
        safe_print("\n" + "=" * 70)
        safe_print("   VIDEO GENERATED!")
        safe_print(f"   File: {output_path}")
        if metadata:
            safe_print(f"   Title: {metadata.get('title', 'N/A')}")
        safe_print("=" * 70)
        
        return output_path
    
    return None


async def upload_video(video_path: str, metadata: Dict) -> Dict:
    """Upload video to platforms."""
    results = {"youtube": None, "dailymotion": None}
    
    title = metadata.get('title', 'Amazing Fact')[:100]
    description = metadata.get('description', 'Follow for more!')[:5000]
    hashtags = metadata.get('hashtags', ['#shorts', '#viral'])
    tags = [h.replace('#', '').strip() for h in hashtags if h]
    
    safe_print(f"\n[UPLOAD] Title: {title}")
    
    try:
        from youtube_uploader import upload_to_youtube
        result = upload_to_youtube(video_path, title=title, description=description, tags=tags)
        if result:
            results["youtube"] = result
            safe_print(f"[OK] YouTube: {result}")
    except Exception as e:
        safe_print(f"[!] YouTube error: {e}")
    
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
    """Generate professional videos with type weighting."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default=None, choices=list(VIDEO_TYPES.keys()) + [None])
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args()
    
    should_upload = args.upload and not args.no_upload
    
    safe_print(f"\n{'='*70}")
    safe_print("   VIRALSHORTS FACTORY v6.0")
    safe_print(f"   Generating {args.count} video(s)")
    safe_print(f"   Types: {list(VIDEO_TYPES.keys())}")
    safe_print(f"{'='*70}")
    
    generated = []
    weight_manager = TypeWeightManager()
    
    for i in range(args.count):
        run_id = int(time.time() * 1000) % 100000 + i
        
        # Use specified type or weighted selection
        video_type = args.type if args.type else weight_manager.get_weighted_type()
        
        safe_print(f"\n{'='*70}")
        safe_print(f"   VIDEO {i+1}/{args.count} - Type: {video_type}")
        safe_print(f"{'='*70}")
        
        path = await generate_pro_video(video_type, run_id)
        if path:
            meta_path = path.replace('.mp4', '_meta.json')
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
            generated.append((path, metadata))
    
    if should_upload and generated:
        safe_print("\n" + "=" * 70)
        safe_print("   UPLOADING TO PLATFORMS")
        safe_print("=" * 70)
        
        for video_path, metadata in generated:
            await upload_video(video_path, metadata)
            if len(generated) > 1:
                delay = random.randint(45, 120)
                safe_print(f"[WAIT] Anti-ban delay: {delay}s")
                time.sleep(delay)
    
    safe_print(f"\n{'='*70}")
    safe_print(f"   COMPLETE: {len(generated)} videos generated")
    safe_print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())

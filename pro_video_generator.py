#!/usr/bin/env python3
"""
ViralShorts Factory - PROFESSIONAL Video Generator v4.0
========================================================

MULTI-STAGE AI CHAINING for MAXIMUM QUALITY:
1. Stage 1: AI generates viral topic with hook
2. Stage 2: AI evaluates and enhances the content
3. Stage 3: AI generates perfect B-roll keywords for each phrase
4. Stage 4: AI generates optimized title/description/tags
5. Stage 5: AI validates final output quality

Each stage uses GOD-TIER prompts designed for viral content.
"""

import os
import sys
import re
import json
import asyncio
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# Core imports
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, ImageClip, CompositeAudioClip,
    ColorClip
)
from moviepy.video.VideoClip import VideoClip
import moviepy.video.fx.all as vfx

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Constants
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BROLL_DIR = Path("./assets/broll")
BROLL_DIR.mkdir(parents=True, exist_ok=True)


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


class MultiStageAI:
    """
    Multi-stage AI content generation with chained prompts.
    
    Each stage refines and improves the content:
    Master Prompt -> AI -> Answer -> Evaluation Prompt -> AI -> Refined Answer -> ...
    """
    
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.gemini_model = None
        
        # Initialize Groq
        if self.groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.groq_key)
                safe_print("[OK] Groq AI initialized")
            except Exception as e:
                safe_print(f"[!] Groq init failed: {e}")
        
        # Initialize Gemini as fallback
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                safe_print("[OK] Gemini AI initialized (fallback)")
            except Exception as e:
                safe_print(f"[!] Gemini init failed: {e}")
    
    def _call_groq(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Call Groq API."""
        if not self.client:
            return None
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            safe_print(f"[!] Groq error: {e}")
            return None
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API as fallback."""
        if not self.gemini_model:
            return None
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            safe_print(f"[!] Gemini error: {e}")
            return None
    
    def call_ai(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call AI with automatic fallback."""
        result = self._call_groq(prompt, max_tokens)
        if not result:
            result = self._call_gemini(prompt)
        if not result:
            return ""
        return result
    
    def parse_json(self, text: str) -> Dict:
        """Extract JSON from AI response."""
        try:
            # Find JSON in response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Clean and parse
            text = text.strip()
            return json.loads(text)
        except:
            return {}
    
    # =========================================================================
    # STAGE 1: Generate Viral Topic
    # =========================================================================
    def stage1_generate_topic(self, video_type: str = None) -> Dict:
        """
        Stage 1: Generate a viral, engaging topic.
        Uses psychology of viral content to create hooks that DEMAND attention.
        """
        safe_print("\n[STAGE 1] Generating viral topic...")
        
        prompt = f"""You are a VIRAL CONTENT MASTERMIND. Your job is to create content that gets 
MILLIONS of views on YouTube Shorts and TikTok.

TODAY'S DATE: {time.strftime('%B %d, %Y')}
DAY OF WEEK: {time.strftime('%A')}
CONTENT TYPE: {video_type or 'psychology_fact'}

=== VIRAL PSYCHOLOGY TRIGGERS ===
1. CURIOSITY GAP: Open a loop the viewer MUST close
2. IDENTITY: Make them feel special/smart for knowing this  
3. FEAR/URGENCY: "You're doing X wrong" / "Before it's too late"
4. SOCIAL PROOF: "97% of people don't know this"
5. CONTRARIAN: Challenge what they believe
6. PRACTICAL VALUE: Give them a superpower

=== YOUR MISSION ===
Create content that:
1. HOOKS in 0.5 seconds (pattern interrupt)
2. DELIVERS real value (not empty promises)
3. Creates SHAREABILITY (they want to tell friends)
4. Ends with DESIRE for more (subscribe trigger)

=== FORMAT REQUIREMENTS (FOR SHORT-FORM VIDEO) ===
- Use DIGITS for numbers (500$ not five hundred dollars)
- Keep sentences SHORT and punchy
- Each phrase should be 8-12 words MAX
- Total content: 4-5 phrases that build on each other

=== OUTPUT (JSON ONLY) ===
{{
    "topic": "The main topic in 5 words",
    "hook": "A 5-10 word pattern-interrupt hook (MUST create curiosity gap)",
    "content_phrases": [
        "First phrase - the setup (8-12 words)",
        "Second phrase - the tension (8-12 words)", 
        "Third phrase - the payoff/value (8-12 words)",
        "Fourth phrase - the reinforcement (8-12 words)"
    ],
    "value_delivered": "What specific value does the viewer get?",
    "psychological_triggers": ["trigger1", "trigger2"],
    "shareability_factor": "Why would someone share this?",
    "video_type": "{video_type or 'psychology_fact'}"
}}

RESPOND WITH JSON ONLY. NO EXTRA TEXT."""

        response = self.call_ai(prompt, 800)
        result = self.parse_json(response)
        
        if result:
            safe_print(f"   Topic: {result.get('topic', 'N/A')}")
            safe_print(f"   Hook: {result.get('hook', 'N/A')}")
            safe_print(f"   Value: {result.get('value_delivered', 'N/A')}")
        
        return result
    
    # =========================================================================
    # STAGE 2: Evaluate and Enhance Content
    # =========================================================================
    def stage2_enhance_content(self, stage1_result: Dict) -> Dict:
        """
        Stage 2: AI evaluates Stage 1 output and enhances it.
        This creates the chaining effect: AI output -> AI enhancement.
        """
        safe_print("\n[STAGE 2] AI evaluating and enhancing content...")
        
        if not stage1_result:
            return {}
        
        prompt = f"""You are a VIRAL CONTENT OPTIMIZER. Your job is to take good content 
and make it EXCEPTIONAL.

=== ORIGINAL CONTENT (from Stage 1) ===
Topic: {stage1_result.get('topic', '')}
Hook: {stage1_result.get('hook', '')}
Phrases: {json.dumps(stage1_result.get('content_phrases', []))}
Value: {stage1_result.get('value_delivered', '')}

=== YOUR OPTIMIZATION TASKS ===

1. HOOK OPTIMIZATION:
   - Is it a TRUE pattern interrupt?
   - Does it create an irresistible curiosity gap?
   - Would YOU stop scrolling for this?
   
2. CONTENT FLOW:
   - Does each phrase build tension?
   - Is there a clear payoff?
   - Are there any "empty" phrases that add nothing?
   
3. VALUE CHECK:
   - Is specific, actionable value delivered?
   - Would the viewer feel smarter after watching?
   - Is there a "oh wow I didn't know that" moment?

4. READABILITY:
   - All numbers as digits (500$, 92%, 3x)
   - No jargon or complex words
   - Each phrase stands alone as readable

=== OUTPUT (JSON ONLY) ===
Return the IMPROVED version:
{{
    "hook": "The optimized hook (even more compelling)",
    "content_phrases": [
        "Enhanced phrase 1",
        "Enhanced phrase 2",
        "Enhanced phrase 3", 
        "Enhanced phrase 4"
    ],
    "improvements_made": ["what you improved"],
    "viral_score": 1-10,
    "ready_for_production": true/false
}}

RESPOND WITH JSON ONLY."""

        response = self.call_ai(prompt, 600)
        result = self.parse_json(response)
        
        if result:
            safe_print(f"   Viral Score: {result.get('viral_score', 'N/A')}/10")
            safe_print(f"   Improvements: {result.get('improvements_made', [])}")
            
            # Merge with stage 1
            stage1_result.update({
                'hook': result.get('hook', stage1_result.get('hook', '')),
                'content_phrases': result.get('content_phrases', stage1_result.get('content_phrases', [])),
                'viral_score': result.get('viral_score', 5)
            })
        
        return stage1_result
    
    # =========================================================================
    # STAGE 3: Generate B-Roll Keywords
    # =========================================================================
    def stage3_broll_keywords(self, content: Dict) -> List[str]:
        """
        Stage 3: Generate SPECIFIC B-roll keywords for each phrase.
        This ensures visuals perfectly match the content.
        """
        safe_print("\n[STAGE 3] Generating visual keywords for each phrase...")
        
        phrases = content.get('content_phrases', [])
        if not phrases:
            return ["dramatic scene", "abstract motion", "person thinking", "success"]
        
        prompt = f"""You are a VISUAL DIRECTOR for viral short videos.
Your job is to select the PERFECT visual for each phrase.

=== CONTENT PHRASES ===
{json.dumps(phrases, indent=2)}

=== VISUAL SELECTION CRITERIA ===
1. Each visual must ENHANCE understanding (not just decorate)
2. Visuals should create EMOTIONAL ESCALATION
3. Think about COLOR PSYCHOLOGY (dark for tension, bright for payoff)
4. Consider MOVEMENT (still for tension, motion for release)

=== B-ROLL SEARCH TIPS ===
- Be SPECIFIC: "person looking at phone in dark room" > "technology"
- Include MOOD: "dramatic cityscape at night" > "city"
- Think EMOTION: "stressed businessman" > "office"

=== OUTPUT (JSON ARRAY ONLY) ===
Return exactly {len(phrases)} keywords, one per phrase:
["keyword for phrase 1", "keyword for phrase 2", ...]

RESPOND WITH JSON ARRAY ONLY."""

        response = self.call_ai(prompt, 300)
        
        try:
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                keywords = json.loads(response[start:end])
                safe_print(f"   Keywords: {keywords}")
                return keywords
        except:
            pass
        
        return ["dramatic scene"] * len(phrases)
    
    # =========================================================================
    # STAGE 4: Generate Viral Metadata
    # =========================================================================
    def stage4_viral_metadata(self, content: Dict) -> Dict:
        """
        Stage 4: Generate viral-optimized title, description, hashtags.
        """
        safe_print("\n[STAGE 4] Generating viral metadata...")
        
        prompt = f"""You are a YOUTUBE SHORTS ALGORITHM EXPERT.
Your job is to create metadata that MAXIMIZES discovery and clicks.

=== CONTENT ===
Topic: {content.get('topic', '')}
Hook: {content.get('hook', '')}
Type: {content.get('video_type', 'fact')}

=== TITLE PSYCHOLOGY ===
1. Create CURIOSITY (what happens next?)
2. Include NUMBERS when relevant (97%, 3 things, $500)
3. Use POWER WORDS (shocking, secret, never, always)
4. Keep under 60 characters
5. Front-load the most compelling part

=== HASHTAG STRATEGY ===
- Mix: 3 trending + 3 niche + 3 broad
- Always include: #shorts #viral #fyp

=== OUTPUT (JSON ONLY) ===
{{
    "title": "The viral-optimized title (under 60 chars)",
    "description": "2-3 sentence description with call to action",
    "hashtags": ["#tag1", "#tag2", ...],
    "thumbnail_text": "3-5 word thumbnail overlay text"
}}

RESPOND WITH JSON ONLY."""

        response = self.call_ai(prompt, 400)
        result = self.parse_json(response)
        
        if result:
            safe_print(f"   Title: {result.get('title', 'N/A')}")
        
        return result


class ProVideoRenderer:
    """
    Professional video rendering with all enhancements.
    """
    
    def __init__(self):
        self.pexels_key = os.environ.get("PEXELS_API_KEY")
        safe_print(f"[OK] Pexels key: {'configured' if self.pexels_key else 'MISSING'}")
    
    def download_broll(self, keyword: str, index: int) -> Optional[str]:
        """Download B-roll from Pexels."""
        import requests
        
        if not self.pexels_key:
            return None
        
        safe_keyword = "".join(c if c.isalnum() or c == '_' else '_' for c in keyword)[:30]
        cache_file = BROLL_DIR / f"pro_{safe_keyword}_{index}.mp4"
        
        if cache_file.exists():
            return str(cache_file)
        
        try:
            headers = {"Authorization": self.pexels_key}
            url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=5"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                safe_print(f"   [!] Pexels error {response.status_code} for '{keyword}'")
                return None
            
            videos = response.json().get("videos", [])
            if not videos:
                safe_print(f"   [!] No videos for '{keyword}'")
                return None
            
            video = random.choice(videos)
            video_files = video.get("video_files", [])
            
            # Get HD quality
            best = None
            for vf in video_files:
                if vf.get("quality") == "hd":
                    best = vf
                    break
            if not best and video_files:
                best = video_files[0]
            
            if not best:
                return None
            
            # Download
            video_url = best.get("link")
            video_response = requests.get(video_url, timeout=60, stream=True)
            
            with open(cache_file, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            safe_print(f"   [OK] Downloaded: {keyword}")
            return str(cache_file)
            
        except Exception as e:
            safe_print(f"   [!] Download error: {e}")
            return None
    
    def create_text_overlay(self, text: str, width: int, height: int) -> Image.Image:
        """Create professional text overlay with clean styling."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Clean text
        text = strip_emojis(text)
        
        # Find font (prioritize Impact for short-form)
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/ariblk.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        font_path = next((f for f in font_paths if os.path.exists(f)), None)
        
        try:
            font = ImageFont.truetype(font_path, 72) if font_path else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Word wrap
        words = text.split()
        lines = []
        current = []
        max_width = width - 120
        
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
        
        # Draw centered
        line_height = 95
        total_height = len(lines) * line_height
        y = (height - total_height) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - (bbox[2] - bbox[0])) // 2
            
            # Black outline (thick for readability)
            for ox in range(-5, 6):
                for oy in range(-5, 6):
                    if ox != 0 or oy != 0:
                        draw.text((x + ox, y + oy), line, fill=(0, 0, 0, 255), font=font)
            
            # White text
            draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
            
            y += line_height
        
        return img
    
    def create_gradient_bg(self, width: int, height: int, colors: Tuple) -> Image.Image:
        """Create gradient background."""
        img = Image.new('RGB', (width, height))
        
        for y in range(height):
            ratio = y / height
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
            
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
        
        return img
    
    def create_progress_bar(self, duration: float) -> VideoClip:
        """Create animated progress bar."""
        bar_height = 6
        
        def make_frame(t):
            progress = t / duration
            frame = np.zeros((bar_height + 4, VIDEO_WIDTH, 3), dtype=np.uint8)
            
            # Background
            frame[2:bar_height+2, :, :] = [40, 40, 40]
            
            # Progress fill (gradient)
            fill_width = int(VIDEO_WIDTH * progress)
            if fill_width > 0:
                for x in range(fill_width):
                    ratio = x / max(fill_width, 1)
                    r = int(255 * (1 - ratio * 0.3))
                    g = int(100 + 155 * ratio)
                    b = 255
                    frame[2:bar_height+2, x, :] = [r, g, b]
            
            return frame
        
        return VideoClip(make_frame, duration=duration)
    
    async def render_video(self, content: Dict, broll_paths: List[str], 
                          output_path: str) -> bool:
        """Render the final video with all enhancements."""
        safe_print("\n[RENDER] Starting professional video render...")
        
        phrases = content.get('content_phrases', [])
        hook = content.get('hook', '')
        
        if not phrases:
            safe_print("[!] No content phrases")
            return False
        
        # Generate voiceover
        full_text = f"{hook}. {' '.join(phrases)}"
        voiceover_path = OUTPUT_DIR / "temp_pro_vo.mp3"
        
        try:
            from script_v2 import generate_voiceover_v2
            duration = await generate_voiceover_v2(full_text, str(voiceover_path))
            safe_print(f"   [OK] Voiceover: {duration:.1f}s")
        except Exception as e:
            safe_print(f"   [!] Voiceover failed: {e}")
            return False
        
        # Calculate phrase timings (hook + phrases)
        all_phrases = [hook] + phrases
        total_words = sum(len(p.split()) for p in all_phrases)
        
        phrase_durations = []
        for phrase in all_phrases:
            word_count = len(phrase.split())
            phrase_duration = (word_count / total_words) * duration
            phrase_duration = max(phrase_duration, 1.5)
            phrase_durations.append(phrase_duration)
        
        # Scale to match actual duration
        total_calc = sum(phrase_durations)
        if total_calc > 0:
            scale = duration / total_calc
            phrase_durations = [d * scale for d in phrase_durations]
        
        # Create segments
        segments = []
        gradient_colors = [
            ((20, 20, 60), (60, 20, 80)),   # Deep purple
            ((10, 30, 50), (30, 60, 90)),   # Ocean
            ((40, 20, 30), (80, 30, 50)),   # Burgundy
            ((20, 40, 40), (40, 80, 80)),   # Teal
        ]
        
        # Ensure we have enough broll paths (add None for hook)
        all_broll = [None] + broll_paths
        while len(all_broll) < len(all_phrases):
            all_broll.append(None)
        
        for i, (phrase, broll_path, dur) in enumerate(zip(all_phrases, all_broll, phrase_durations)):
            safe_print(f"   [*] Segment {i+1}/{len(all_phrases)}: {phrase[:30]}...")
            
            layers = []
            
            # Background (B-roll or gradient)
            if broll_path and os.path.exists(broll_path):
                try:
                    bg = VideoFileClip(broll_path)
                    bg = bg.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
                    if bg.duration < dur:
                        bg = bg.loop(duration=dur)
                    bg = bg.subclip(0, dur)
                    bg = bg.fx(vfx.colorx, 0.55)  # Darken for text
                    layers.append(bg)
                except Exception as e:
                    broll_path = None
            
            if not broll_path:
                colors = random.choice(gradient_colors)
                gradient = self.create_gradient_bg(VIDEO_WIDTH, VIDEO_HEIGHT, colors)
                from script_v2 import pil_to_moviepy_clip
                bg = pil_to_moviepy_clip(gradient, dur)
                layers.append(bg)
            
            # Text overlay
            text_img = self.create_text_overlay(phrase, VIDEO_WIDTH, VIDEO_HEIGHT // 2)
            from script_v2 import pil_to_moviepy_clip
            text_clip = pil_to_moviepy_clip(text_img, dur)
            text_clip = text_clip.set_position(('center', 'center'))
            layers.append(text_clip)
            
            # Compose segment
            segment = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
            segment = segment.set_duration(dur)
            segments.append(segment)
        
        # Concatenate
        safe_print("   [*] Concatenating segments...")
        final_video = concatenate_videoclips(segments, method="compose")
        
        # Add progress bar
        safe_print("   [*] Adding progress bar...")
        progress_clip = self.create_progress_bar(final_video.duration)
        progress_clip = progress_clip.set_position(("center", 15))
        
        final_video = CompositeVideoClip(
            [final_video, progress_clip],
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        ).set_duration(final_video.duration)
        
        # Add audio
        vo_clip = AudioFileClip(str(voiceover_path))
        
        # Background music
        music_clip = None
        try:
            from background_music import get_background_music
            music_path = get_background_music("dramatic")
            if music_path and os.path.exists(music_path):
                music_clip = AudioFileClip(music_path)
                music_clip = music_clip.volumex(0.12)
                safe_print("   [OK] Added background music")
        except:
            pass
        
        # Mix audio
        if music_clip:
            if music_clip.duration < final_video.duration:
                music_clip = music_clip.loop(duration=final_video.duration)
            music_clip = music_clip.subclip(0, final_video.duration)
            final_audio = CompositeAudioClip([vo_clip, music_clip])
        else:
            final_audio = vo_clip
        
        final_video = final_video.set_audio(final_audio)
        
        # Render
        safe_print("   [*] Rendering final video...")
        final_video.write_videofile(
            output_path,
            fps=30,  # Higher FPS for smoothness
            codec='libx264',
            audio_codec='aac',
            preset='medium',  # Better quality
            bitrate='8M',     # Higher bitrate
            threads=4
        )
        
        safe_print(f"   [OK] Created: {output_path}")
        return True


async def generate_pro_video(video_type: str = "psychology_fact") -> Optional[str]:
    """
    Generate a professional video using multi-stage AI chaining.
    """
    safe_print("=" * 70)
    safe_print("   PROFESSIONAL VIDEO GENERATOR v4.0")
    safe_print("   Multi-Stage AI Chaining for Maximum Quality")
    safe_print("=" * 70)
    
    # Initialize AI
    ai = MultiStageAI()
    if not ai.client and not ai.gemini_model:
        safe_print("[!] No AI available - check GROQ_API_KEY or GEMINI_API_KEY")
        return None
    
    # Stage 1: Generate Topic
    stage1 = ai.stage1_generate_topic(video_type)
    if not stage1:
        safe_print("[!] Stage 1 failed")
        return None
    
    # Stage 2: Enhance Content
    stage2 = ai.stage2_enhance_content(stage1)
    if not stage2:
        safe_print("[!] Stage 2 failed")
        return None
    
    # Stage 3: B-roll Keywords
    broll_keywords = ai.stage3_broll_keywords(stage2)
    
    # Stage 4: Viral Metadata
    metadata = ai.stage4_viral_metadata(stage2)
    
    # Download B-roll
    safe_print("\n[BROLL] Downloading visuals...")
    renderer = ProVideoRenderer()
    broll_paths = []
    for i, keyword in enumerate(broll_keywords):
        path = renderer.download_broll(keyword, i)
        broll_paths.append(path)
    
    # Render video
    video_id = random.randint(1000, 9999)
    output_path = str(OUTPUT_DIR / f"pro_{video_type}_{video_id}.mp4")
    
    success = await renderer.render_video(stage2, broll_paths, output_path)
    
    if success:
        # Save metadata
        meta_path = output_path.replace('.mp4', '_meta.json')
        with open(meta_path, 'w') as f:
            json.dump({
                'content': stage2,
                'metadata': metadata,
                'broll_keywords': broll_keywords
            }, f, indent=2)
        
        safe_print("\n" + "=" * 70)
        safe_print("   VIDEO GENERATED SUCCESSFULLY!")
        safe_print(f"   File: {output_path}")
        if metadata:
            safe_print(f"   Title: {metadata.get('title', 'N/A')}")
        safe_print("=" * 70)
        
        return output_path
    
    return None


async def upload_video(video_path: str, metadata: Dict) -> Dict:
    """Upload video to YouTube and Dailymotion."""
    results = {"youtube": None, "dailymotion": None}
    
    title = metadata.get('title', 'Amazing Fact You Need to Know')[:100]
    description = metadata.get('description', 'Follow for more amazing content!')[:5000]
    hashtags = metadata.get('hashtags', ['#shorts', '#viral', '#facts', '#fyp'])
    tags = [h.replace('#', '').strip() for h in hashtags if h]
    
    safe_print(f"\n[UPLOAD] Title: {title}")
    
    # YouTube
    try:
        from youtube_uploader import upload_to_youtube
        result = upload_to_youtube(video_path, title=title, description=description, tags=tags)
        if result:
            results["youtube"] = result
            safe_print(f"[OK] YouTube: {result}")
    except Exception as e:
        safe_print(f"[!] YouTube error: {e}")
    
    # Dailymotion
    try:
        from dailymotion_uploader import DailymotionUploader
        dm = DailymotionUploader()
        if dm.is_configured:
            conn = dm.check_connectivity()
            if conn.get('status') == 'ok':
                result = dm.upload_video(
                    video_path, 
                    title=title, 
                    description=description, 
                    tags=tags,
                    channel='lifestyle',
                    ai_generated=False
                )
                if result:
                    results["dailymotion"] = result
                    safe_print(f"[OK] Dailymotion: {result}")
    except Exception as e:
        safe_print(f"[!] Dailymotion error: {e}")
    
    return results


async def main():
    """Generate and optionally upload professional videos."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="psychology_fact", 
                       choices=["psychology_fact", "money_fact", "life_hack", "scary_fact"])
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--upload", action="store_true", help="Upload to platforms")
    parser.add_argument("--no-upload", action="store_true", help="Skip upload")
    args = parser.parse_args()
    
    should_upload = args.upload and not args.no_upload
    
    safe_print(f"\nGenerating {args.count} professional video(s)...")
    if should_upload:
        safe_print("[MODE] Will upload after generation")
    else:
        safe_print("[MODE] Local generation only (no upload)")
    
    generated_videos = []
    
    for i in range(args.count):
        safe_print(f"\n{'='*70}")
        safe_print(f"   VIDEO {i+1}/{args.count}")
        safe_print(f"{'='*70}")
        
        path = await generate_pro_video(args.type)
        if path:
            safe_print(f"\n[DONE] Video saved: {path}")
            
            # Load metadata
            meta_path = path.replace('.mp4', '_meta.json')
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
            
            generated_videos.append((path, metadata))
        else:
            safe_print("\n[FAIL] Video generation failed")
    
    # Upload if requested
    if should_upload and generated_videos:
        safe_print("\n" + "=" * 70)
        safe_print("   UPLOADING TO PLATFORMS")
        safe_print("=" * 70)
        
        for video_path, metadata in generated_videos:
            await upload_video(video_path, metadata)
            
            # Anti-ban delay between uploads
            if len(generated_videos) > 1:
                delay = random.randint(30, 90)
                safe_print(f"[WAIT] Anti-ban delay: {delay}s")
                time.sleep(delay)
    
    safe_print("\n" + "=" * 70)
    safe_print(f"   COMPLETE: {len(generated_videos)} videos generated")
    safe_print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())


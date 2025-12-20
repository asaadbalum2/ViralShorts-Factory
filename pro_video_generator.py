#!/usr/bin/env python3
"""
ViralShorts Factory - PROFESSIONAL Video Generator v7.0
========================================================

100% AI-DRIVEN - NO HARDCODING!

Core Philosophy:
- Master Prompt -> AI -> Answer -> Evaluation -> AI -> Refined Answer
- AI decides: video type, phrase count, content length, music mood, voice style
- AI evaluates: value delivery, viral potential, comprehensiveness
- Everything flows through AI, nothing is hardcoded

This system asks AI for EVERYTHING and only uses hardcoded values as absolute fallbacks.
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


class MasterAI:
    """
    100% AI-Driven Content System
    
    NO HARDCODING. Everything is decided by AI through chained prompts.
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
    
    # =========================================================================
    # STAGE 1: AI Decides What Type of Video to Create
    # =========================================================================
    def stage1_decide_video_concept(self, hint: str = None) -> Dict:
        """
        AI decides EVERYTHING about the video concept.
        No hardcoded types - AI generates based on what's trending/viral.
        """
        safe_print("\n[STAGE 1] AI deciding video concept...")
        
        unique_seed = f"{time.time()}_{random.random()}"
        hint_text = f"User hint: {hint}" if hint else "No specific hint - create something viral and valuable"
        
        prompt = f"""You are a VIRAL CONTENT STRATEGIST for short-form video (YouTube Shorts, TikTok).
Your job is to decide what video to create that will get MAXIMUM views while delivering REAL value.

UNIQUE GENERATION ID: {unique_seed}
DATE: {time.strftime('%B %d, %Y, %A')}
{hint_text}

=== YOUR DECISION TASKS ===

1. **VIDEO CATEGORY**: What category will perform best right now?
   Consider: psychology, finance, life hacks, science, motivation, relationships, 
   productivity, health, technology, history, statistics, mysteries, etc.
   Pick ONE that you believe will be most viral TODAY.

2. **SPECIFIC TOPIC**: Within that category, what specific topic?
   Must be: Surprising, valuable, shareable, globally relevant

3. **CONTENT LENGTH**: How many phrases/sections should the video have?
   Consider: For simple facts = 4-5 phrases, for tutorials = 6-8 phrases
   Match length to content complexity. Longer = more value, but must stay engaging.

4. **VOICE STYLE**: What voice/energy for the narration?
   Options: energetic, calm, mysterious, authoritative, friendly, dramatic

5. **MUSIC MOOD**: What background music mood?
   Options: upbeat, dramatic, mysterious, inspirational, chill, intense

6. **TARGET DURATION**: How long should the video be?
   Options: 15-20s (quick fact), 25-35s (explained fact), 40-50s (mini-tutorial)

=== OUTPUT JSON ===
{{
    "category": "the video category",
    "specific_topic": "the specific topic (5-10 words)",
    "why_this_topic": "why this will be viral and valuable",
    "phrase_count": 5,  // number between 4-8 based on content needs
    "voice_style": "energetic/calm/mysterious/etc",
    "music_mood": "upbeat/dramatic/mysterious/etc",
    "target_duration_seconds": 30,
    "global_relevance": "why this works worldwide"
}}

OUTPUT JSON ONLY. Be creative and strategic!"""

        response = self.call_ai(prompt, 800, temperature=0.95)
        result = self.parse_json(response)
        
        if result:
            safe_print(f"   Category: {result.get('category', 'N/A')}")
            safe_print(f"   Topic: {result.get('specific_topic', 'N/A')}")
            safe_print(f"   Phrases: {result.get('phrase_count', 'N/A')}")
            safe_print(f"   Duration: ~{result.get('target_duration_seconds', 'N/A')}s")
        
        return result
    
    # =========================================================================
    # STAGE 2: AI Creates the Content Based on Its Own Decisions
    # =========================================================================
    def stage2_create_content(self, concept: Dict) -> Dict:
        """
        AI creates the actual content based on the concept it decided.
        """
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
- Phrase 1: HOOK (pattern interrupt, curiosity)
- Phrases 2-{phrase_count-1}: BUILD (problem, context, solution parts)
- Phrase {phrase_count}: PAYOFF (transformation, call to action)

=== OUTPUT JSON ===
{{
    "phrases": [
        "Phrase 1: The hook...",
        "Phrase 2: ...",
        // ... exactly {phrase_count} phrases
    ],
    "specific_value": "What SPECIFIC action can viewer take after watching?",
    "problem_solved": "What problem did we solve?",
    "solution_given": "What specific solution did we provide?"
}}

OUTPUT JSON ONLY. Make every phrase count!"""

        response = self.call_ai(prompt, 1200, temperature=0.85)
        result = self.parse_json(response)
        
        if result and result.get('phrases'):
            result['concept'] = concept
            safe_print(f"   Created {len(result.get('phrases', []))} phrases")
            safe_print(f"   Value: {result.get('specific_value', 'N/A')[:60]}...")
        
        return result
    
    # =========================================================================
    # STAGE 3: AI Evaluates and Enhances the Content
    # =========================================================================
    def stage3_evaluate_enhance(self, content: Dict) -> Dict:
        """
        AI evaluates its own content and improves it.
        Master Prompt -> AI -> Answer -> Evaluation Prompt -> AI -> Better Answer
        """
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
        "Improved phrase 1",
        "Improved phrase 2",
        // same count as input
    ],
    "final_value_delivered": "What specific value does viewer get now?"
}}

OUTPUT JSON ONLY."""

        response = self.call_ai(prompt, 1000, temperature=0.7)
        result = self.parse_json(response)
        
        if result:
            content['phrases'] = result.get('improved_phrases', content.get('phrases', []))
            content['evaluation_score'] = result.get('evaluation_score', 7)
            content['value_delivered'] = result.get('final_value_delivered', '')
            safe_print(f"   Score: {result.get('evaluation_score', 'N/A')}/10")
            if result.get('improvements_made'):
                safe_print(f"   Improvements: {result.get('improvements_made', [])[:2]}")
        
        return content
    
    # =========================================================================
    # STAGE 4: AI Generates B-Roll Keywords
    # =========================================================================
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
    
    # =========================================================================
    # STAGE 5: AI Generates Metadata
    # =========================================================================
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
    
    # =========================================================================
    # STAGE 6: AI Decides Voice and Music Based on Content
    # =========================================================================
    def get_voice_config(self, concept: Dict) -> Dict:
        """Get voice configuration based on AI-decided style."""
        voice_style = concept.get('voice_style', 'energetic').lower()
        
        # Map styles to voices (these are technical mappings, not content)
        voice_map = {
            'energetic': ('en-US-AriaNeural', '+8%'),
            'calm': ('en-US-JennyNeural', '-3%'),
            'mysterious': ('en-US-GuyNeural', '-5%'),
            'authoritative': ('en-US-DavisNeural', '+0%'),
            'friendly': ('en-US-AriaNeural', '+5%'),
            'dramatic': ('en-US-ChristopherNeural', '-3%'),
        }
        
        voice, rate = voice_map.get(voice_style, ('en-US-AriaNeural', '+0%'))
        return {'voice': voice, 'rate': rate}


class VideoRenderer:
    """Professional video rendering."""
    
    def __init__(self):
        self.pexels_key = os.environ.get("PEXELS_API_KEY")
    
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
        """Convert PIL to MoviePy clip."""
        arr = np.array(pil_img.convert('RGBA'))
        return ImageClip(arr, duration=duration, ismask=False)


def get_background_music_with_skip(mood: str, skip_seconds: float = 3.0) -> Optional[Tuple[str, float]]:
    """
    Get background music and skip the silent intro.
    Returns (path, skip_seconds) to skip silent beginning.
    """
    try:
        from background_music import get_background_music
        music_path = get_background_music(mood)
        if music_path:
            # Skip first 3 seconds to avoid silent intro
            return (music_path, skip_seconds)
    except:
        pass
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


async def render_video(content: Dict, broll_paths: List[str], output_path: str) -> bool:
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
    
    # Get AI-decided voice config
    ai = MasterAI()
    voice_config = ai.get_voice_config(concept)
    
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
    
    # Get music with intro skip
    music_mood = concept.get('music_mood', 'dramatic')
    music_result = get_background_music_with_skip(music_mood, skip_seconds=3.0)
    if music_result:
        safe_print(f"   [OK] Music: {music_mood} (skipping first 3s)")
    
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
                bg = bg.fx(vfx.colorx, 0.5)
                
                layers.append(bg)
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
        
        text_img = renderer.create_text_overlay(phrase, VIDEO_WIDTH, VIDEO_HEIGHT // 2)
        text_clip = renderer.pil_to_clip(text_img, dur)
        text_clip = text_clip.set_position(('center', 'center'))
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
    
    # Audio mixing - skip music intro
    vo_clip = AudioFileClip(voiceover_path)
    
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
            
            final_audio = CompositeAudioClip([vo_clip, music_clip])
        except Exception as e:
            safe_print(f"   [!] Music error: {e}")
            final_audio = vo_clip
    else:
        final_audio = vo_clip
    
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


async def generate_pro_video(hint: str = None) -> Optional[str]:
    """
    Generate a video with 100% AI-driven decisions.
    No hardcoding - AI decides everything.
    """
    run_id = random.randint(10000, 99999)
    
    safe_print("=" * 70)
    safe_print(f"   VIRALSHORTS FACTORY v7.0 - 100% AI-DRIVEN")
    safe_print(f"   Run: #{run_id}")
    safe_print("=" * 70)
    
    ai = MasterAI()
    if not ai.client and not ai.gemini_model:
        safe_print("[!] No AI available")
        return None
    
    # Stage 1: AI decides concept
    concept = ai.stage1_decide_video_concept(hint)
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
    
    success = await render_video(content, broll_paths, output_path)
    
    if success:
        meta_path = output_path.replace('.mp4', '_meta.json')
        with open(meta_path, 'w') as f:
            json.dump({
                'concept': concept,
                'content': content,
                'metadata': metadata,
                'broll_keywords': broll_keywords,
                'run_id': run_id
            }, f, indent=2)
        
        safe_print("\n" + "=" * 70)
        safe_print("   VIDEO GENERATED!")
        safe_print(f"   File: {output_path}")
        safe_print(f"   Category: {concept.get('category', 'N/A')}")
        safe_print(f"   Score: {content.get('evaluation_score', 'N/A')}/10")
        if metadata:
            safe_print(f"   Title: {metadata.get('title', 'N/A')}")
        safe_print("=" * 70)
        
        return output_path
    
    return None


async def upload_video(video_path: str, metadata: Dict) -> Dict:
    """Upload to platforms."""
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
    """Generate videos with 100% AI decision-making."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--hint", default=None, help="Optional hint for AI (e.g., 'psychology', 'money')")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    # Legacy support - these are IGNORED, AI decides
    parser.add_argument("--type", default=None, help="IGNORED - AI decides type")
    args = parser.parse_args()
    
    should_upload = args.upload and not args.no_upload
    
    safe_print(f"\n{'='*70}")
    safe_print("   VIRALSHORTS FACTORY v7.0 - 100% AI-DRIVEN")
    safe_print(f"   Generating {args.count} video(s)")
    safe_print("   AI decides: category, topic, length, voice, music")
    safe_print(f"{'='*70}")
    
    # Use hint if provided (or from legacy --type)
    hint = args.hint or args.type
    
    generated = []
    
    for i in range(args.count):
        safe_print(f"\n{'='*70}")
        safe_print(f"   VIDEO {i+1}/{args.count}")
        safe_print(f"{'='*70}")
        
        path = await generate_pro_video(hint)
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
        safe_print("   UPLOADING")
        safe_print("=" * 70)
        
        for video_path, metadata in generated:
            await upload_video(video_path, metadata)
            if len(generated) > 1:
                delay = random.randint(45, 120)
                safe_print(f"[WAIT] Anti-ban delay: {delay}s")
                time.sleep(delay)
    
    safe_print(f"\n{'='*70}")
    safe_print(f"   COMPLETE: {len(generated)} videos")
    safe_print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())

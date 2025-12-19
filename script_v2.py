#!/usr/bin/env python3
"""
QuizBot V2 - Professional Viral "Would You Rather" Video Generator
Complete ground-up rebuild for 10/10 quality

Key improvements:
- Professional visual design with gradients and modern UI
- Dynamic B-roll integration from Pexels API
- Trending topic integration
- Smooth animations and transitions
- Professional typography
- Engagement hooks (subscribe, follow prompts)
- Sound design with background music
- Multiple visual styles/themes
"""

import asyncio
import json
import os
import random
import sys
import hashlib
import time
import math
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import requests

# Fix Pillow 10+ compatibility
from PIL import Image, ImageDraw, ImageFont, ImageFilter
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# Configure ImageMagick for Windows
if sys.platform == "win32":
    import shutil
    magick_paths = [
        r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        shutil.which("magick"),
    ]
    for path in magick_paths:
        if path and os.path.exists(path):
            os.environ["IMAGEMAGICK_BINARY"] = path
            break

import edge_tts
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip, ImageClip,
    CompositeVideoClip, ColorClip, CompositeAudioClip,
    concatenate_videoclips, vfx
)

# ============ CONFIGURATION ============
OUTPUT_DIR = Path("./output")
ASSETS_DIR = Path("./assets")
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
BROLL_DIR = ASSETS_DIR / "broll"
MUSIC_DIR = ASSETS_DIR / "music"
SFX_DIR = ASSETS_DIR / "sfx"
FONTS_DIR = ASSETS_DIR / "fonts"
QUESTIONS_FILE = Path("./questions.json")
CACHE_DIR = Path("./cache")

# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30  # Smoother playback
TARGET_DURATION = 45  # Optimal for Shorts engagement

# Voice settings - ENGAGING, energetic voices for viral content
VOICES = [
    "en-US-ChristopherNeural",  # Confident, clear male
    "en-US-JennyNeural",        # Friendly, upbeat female
    "en-US-AriaNeural",         # Expressive, dramatic female
    "en-US-GuyNeural",          # Casual, relatable male
    "en-US-SaraNeural",         # Warm, engaging female
]

# Voice styles for more personality
VOICE_STYLES = {
    "en-US-AriaNeural": "cheerful",
    "en-US-JennyNeural": "excited",
    "en-US-SaraNeural": "friendly",
}

# Pexels API for B-roll
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")


@dataclass
class VideoTheme:
    """Visual theme configuration"""
    name: str
    primary_color: Tuple[int, int, int]
    secondary_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    gradient_start: Tuple[int, int, int]
    gradient_end: Tuple[int, int, int]
    option_a_gradient: List[Tuple[int, int, int]]
    option_b_gradient: List[Tuple[int, int, int]]
    text_color: Tuple[int, int, int]
    font_name: str


# Professional theme presets
THEMES = {
    "neon_night": VideoTheme(
        name="Neon Night",
        primary_color=(255, 0, 128),
        secondary_color=(0, 255, 255),
        accent_color=(255, 255, 0),
        gradient_start=(15, 0, 36),
        gradient_end=(0, 0, 0),
        option_a_gradient=[(255, 0, 128), (255, 0, 60)],
        option_b_gradient=[(0, 191, 255), (0, 128, 255)],
        text_color=(255, 255, 255),
        font_name="Impact"
    ),
    "fire_ice": VideoTheme(
        name="Fire & Ice",
        primary_color=(255, 69, 0),
        secondary_color=(0, 191, 255),
        accent_color=(255, 215, 0),
        gradient_start=(20, 20, 40),
        gradient_end=(0, 0, 0),
        option_a_gradient=[(255, 69, 0), (255, 140, 0)],
        option_b_gradient=[(0, 191, 255), (30, 144, 255)],
        text_color=(255, 255, 255),
        font_name="Impact"
    ),
    "midnight_purple": VideoTheme(
        name="Midnight Purple",
        primary_color=(138, 43, 226),
        secondary_color=(255, 105, 180),
        accent_color=(0, 255, 127),
        gradient_start=(25, 0, 51),
        gradient_end=(0, 0, 20),
        option_a_gradient=[(138, 43, 226), (75, 0, 130)],
        option_b_gradient=[(255, 105, 180), (255, 20, 147)],
        text_color=(255, 255, 255),
        font_name="Impact"
    ),
    "electric_blue": VideoTheme(
        name="Electric Blue",
        primary_color=(0, 150, 255),
        secondary_color=(0, 255, 200),
        accent_color=(255, 255, 0),
        gradient_start=(0, 20, 40),
        gradient_end=(0, 0, 0),
        option_a_gradient=[(0, 150, 255), (0, 100, 200)],
        option_b_gradient=[(0, 255, 200), (0, 200, 150)],
        text_color=(255, 255, 255),
        font_name="Impact"
    ),
    "sunset_vibes": VideoTheme(
        name="Sunset Vibes",
        primary_color=(255, 99, 71),
        secondary_color=(255, 165, 0),
        accent_color=(255, 215, 0),
        gradient_start=(40, 20, 30),
        gradient_end=(0, 0, 0),
        option_a_gradient=[(255, 99, 71), (255, 69, 0)],
        option_b_gradient=[(255, 165, 0), (255, 200, 0)],
        text_color=(255, 255, 255),
        font_name="Impact"
    ),
}


def ensure_directories():
    """Create necessary directories."""
    for d in [OUTPUT_DIR, ASSETS_DIR, BACKGROUNDS_DIR, BROLL_DIR, 
              MUSIC_DIR, SFX_DIR, FONTS_DIR, CACHE_DIR]:
        d.mkdir(exist_ok=True, parents=True)


def create_gradient_background(width: int, height: int, 
                                color_start: Tuple[int, int, int],
                                color_end: Tuple[int, int, int]) -> Image.Image:
    """Create a smooth vertical gradient background."""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    for y in range(height):
        ratio = y / height
        r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
        g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
        b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img


def create_option_panel_image(width: int, height: int, 
                               gradient_colors: List[Tuple[int, int, int]],
                               option_text: str, 
                               label: str,
                               position: str = "top") -> Image.Image:
    """Create a MODERN, visually appealing option panel with rounded corners and effects."""
    # Margins for modern look (not edge-to-edge ugly squares)
    margin_x = 50
    margin_y = 20
    inner_width = width - (margin_x * 2)
    inner_height = height - (margin_y * 2)
    corner_radius = 40  # Nice rounded corners
    
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # Create the rounded panel
    panel = Image.new('RGBA', (inner_width, inner_height), (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    
    # Create rounded rectangle mask
    mask = Image.new('L', (inner_width, inner_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (inner_width - 1, inner_height - 1)],
        radius=corner_radius,
        fill=255
    )
    
    # Create gradient on panel
    for y in range(inner_height):
        ratio = y / inner_height
        r = int(gradient_colors[0][0] * (1 - ratio) + gradient_colors[1][0] * ratio)
        g = int(gradient_colors[0][1] * (1 - ratio) + gradient_colors[1][1] * ratio)
        b = int(gradient_colors[0][2] * (1 - ratio) + gradient_colors[1][2] * ratio)
        panel_draw.line([(0, y), (inner_width, y)], fill=(r, g, b, 240))
    
    # Apply rounded corners
    panel.putalpha(mask)
    
    # Add drop shadow for depth
    shadow = Image.new('RGBA', (inner_width + 20, inner_height + 20), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [(10, 10), (inner_width + 9, inner_height + 9)],
        radius=corner_radius,
        fill=(0, 0, 0, 100)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    
    # Paste shadow then panel
    img.paste(shadow, (margin_x - 10, margin_y), shadow)
    img.paste(panel, (margin_x, margin_y), panel)
    
    # Add glossy shine effect at top
    shine = Image.new('RGBA', (inner_width - 20, 40), (0, 0, 0, 0))
    shine_draw = ImageDraw.Draw(shine)
    for y in range(40):
        alpha = int(60 * (1 - y / 40))
        shine_draw.line([(0, y), (inner_width - 20, y)], fill=(255, 255, 255, alpha))
    img.paste(shine, (margin_x + 10, margin_y + 5), shine)
    
    draw = ImageDraw.Draw(img)
    
    # Load font (try to use a better font, fallback to default)
    try:
        # Try to load a bold font
        font_size_label = 48
        font_size_text = 56
        font_path = None
        
        # Check for fonts
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        
        for fp in font_candidates:
            if os.path.exists(fp):
                font_path = fp
                break
        
        if font_path:
            font_label = ImageFont.truetype(font_path, font_size_label)
            font_text = ImageFont.truetype(font_path, font_size_text)
        else:
            font_label = ImageFont.load_default()
            font_text = ImageFont.load_default()
    except Exception:
        font_label = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # Draw label (A or B)
    label_y = 30 if position == "top" else height - 80
    bbox = draw.textbbox((0, 0), label, font=font_label)
    label_width = bbox[2] - bbox[0]
    draw.text(((width - label_width) // 2, label_y), label, 
              fill=(255, 255, 255, 255), font=font_label)
    
    # Word wrap the option text
    words = option_text.split()
    lines = []
    current_line = []
    max_chars = 25
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if len(test_line) <= max_chars:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw wrapped text centered
    line_height = 65
    total_text_height = len(lines) * line_height
    start_y = (height - total_text_height) // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_text)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + i * line_height
        
        # Draw text shadow
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0, 180), font=font_text)
        # Draw main text
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font_text)
    
    return img


def create_vs_badge(size: int = 120, theme: VideoTheme = None) -> Image.Image:
    """Create an animated-ready VS badge."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw glowing circle
    center = size // 2
    accent = theme.accent_color if theme else (255, 215, 0)
    
    # Outer glow
    for i in range(10, 0, -1):
        alpha = int(25 * (10 - i) / 10)
        r = center - 5 + i * 3
        draw.ellipse([center - r, center - r, center + r, center + r],
                     fill=(*accent, alpha))
    
    # Main circle
    r = center - 10
    draw.ellipse([center - r, center - r, center + r, center + r],
                 fill=(*accent, 255))
    
    # VS text
    try:
        font_path = "C:/Windows/Fonts/impact.ttf" if sys.platform == "win32" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 50)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), "VS", font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 5
    
    draw.text((x + 2, y + 2), "VS", fill=(0, 0, 0, 150), font=font)
    draw.text((x, y), "VS", fill=(0, 0, 0, 255), font=font)
    
    return img


def create_countdown_frame(number: int, size: int = 200, 
                           theme: VideoTheme = None) -> Image.Image:
    """Create a countdown number frame."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    accent = theme.accent_color if theme else (255, 215, 0)
    
    # Draw pulsing circle
    r = center - 20
    draw.ellipse([center - r, center - r, center + r, center + r],
                 fill=(*accent, 200), outline=(255, 255, 255, 255), width=4)
    
    # Number
    try:
        font_path = "C:/Windows/Fonts/impact.ttf" if sys.platform == "win32" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 100)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 10
    
    draw.text((x, y), text, fill=(0, 0, 0, 255), font=font)
    
    return img


def create_percentage_reveal_frame(percent_a: int, percent_b: int,
                                    width: int, height: int,
                                    theme: VideoTheme) -> Image.Image:
    """Create the percentage reveal overlay."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font_path = "C:/Windows/Fonts/impact.ttf" if sys.platform == "win32" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path):
            font_large = ImageFont.truetype(font_path, 150)
            font_small = ImageFont.truetype(font_path, 50)
        else:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw percentages with glow effect
    # Option A percentage (top half)
    text_a = f"{percent_a}%"
    bbox = draw.textbbox((0, 0), text_a, font=font_large)
    text_width = bbox[2] - bbox[0]
    x_a = (width - text_width) // 2
    y_a = height // 4 - 50
    
    # Glow
    for offset in range(10, 0, -2):
        alpha = int(30 * (10 - offset) / 10)
        draw.text((x_a - offset, y_a), text_a, 
                  fill=(*theme.option_a_gradient[0], alpha), font=font_large)
        draw.text((x_a + offset, y_a), text_a,
                  fill=(*theme.option_a_gradient[0], alpha), font=font_large)
    
    draw.text((x_a + 4, y_a + 4), text_a, fill=(0, 0, 0, 200), font=font_large)
    draw.text((x_a, y_a), text_a, fill=(255, 255, 255, 255), font=font_large)
    
    # Option B percentage (bottom half)
    text_b = f"{percent_b}%"
    bbox = draw.textbbox((0, 0), text_b, font=font_large)
    text_width = bbox[2] - bbox[0]
    x_b = (width - text_width) // 2
    y_b = 3 * height // 4 - 50
    
    # Glow
    for offset in range(10, 0, -2):
        alpha = int(30 * (10 - offset) / 10)
        draw.text((x_b - offset, y_b), text_b,
                  fill=(*theme.option_b_gradient[0], alpha), font=font_large)
        draw.text((x_b + offset, y_b), text_b,
                  fill=(*theme.option_b_gradient[0], alpha), font=font_large)
    
    draw.text((x_b + 4, y_b + 4), text_b, fill=(0, 0, 0, 200), font=font_large)
    draw.text((x_b, y_b), text_b, fill=(255, 255, 255, 255), font=font_large)
    
    return img


def create_hook_text(width: int, height: int, text: str,
                     theme: VideoTheme) -> Image.Image:
    """Create attention-grabbing hook text."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font_path = "C:/Windows/Fonts/impact.ttf" if sys.platform == "win32" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 70)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = 150
    
    # Glow effect
    for offset in range(8, 0, -2):
        alpha = int(40 * (8 - offset) / 8)
        draw.text((x, y - offset), text, fill=(*theme.accent_color, alpha), font=font)
        draw.text((x, y + offset), text, fill=(*theme.accent_color, alpha), font=font)
    
    draw.text((x + 3, y + 3), text, fill=(0, 0, 0, 200), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    return img


def create_cta_text(width: int, height: int, theme: VideoTheme) -> Image.Image:
    """Create call-to-action overlay."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font_path = "C:/Windows/Fonts/impact.ttf" if sys.platform == "win32" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 40)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    text = "👆 FOLLOW FOR MORE! 👆"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = height - 150
    
    # Background pill
    padding = 20
    pill_rect = [x - padding, y - padding // 2, 
                 x + text_width + padding, y + 50 + padding // 2]
    draw.rounded_rectangle(pill_rect, radius=25, fill=(*theme.accent_color, 220))
    
    draw.text((x, y), text, fill=(0, 0, 0, 255), font=font)
    
    return img


def download_pexels_video(query: str, output_path: str) -> bool:
    """Download a video from Pexels API based on query."""
    if not PEXELS_API_KEY:
        print("   ⚠️ No Pexels API key, using fallback background")
        return False
    
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        # Search for vertical videos
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=10"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"   ⚠️ Pexels API error: {response.status_code}")
            return False
        
        data = response.json()
        videos = data.get("videos", [])
        
        if not videos:
            print(f"   ⚠️ No videos found for: {query}")
            return False
        
        # Pick a random video
        video = random.choice(videos)
        video_files = video.get("video_files", [])
        
        # Find HD quality
        best_file = None
        for vf in video_files:
            if vf.get("height", 0) >= 720:
                if best_file is None or vf.get("height", 0) > best_file.get("height", 0):
                    best_file = vf
        
        if not best_file:
            best_file = video_files[0] if video_files else None
        
        if not best_file:
            return False
        
        # Download video
        video_url = best_file.get("link")
        print(f"   📥 Downloading B-roll: {query}...")
        video_response = requests.get(video_url, timeout=60)
        
        with open(output_path, 'wb') as f:
            f.write(video_response.content)
        
        print(f"   ✅ Downloaded: {output_path}")
        return True
        
    except Exception as e:
        print(f"   ⚠️ Pexels download error: {e}")
        return False


def get_broll_for_question(question: dict) -> Optional[str]:
    """Get relevant B-roll video for the question."""
    # FIRST: Check if we have ANY B-roll files already downloaded
    if BROLL_DIR.exists():
        broll_files = list(BROLL_DIR.glob("*.mp4"))
        if broll_files:
            # Pick a random one
            chosen = random.choice(broll_files)
            print(f"   ✅ Using B-roll: {chosen.name}")
            return str(chosen)
    
    # Extract keywords from the question
    option_a = question.get("option_a", "")
    option_b = question.get("option_b", "")
    
    # Common keyword mappings
    keywords = []
    text = f"{option_a} {option_b}".lower()
    
    keyword_map = {
        "money": ["money", "wealth", "luxury"],
        "travel": ["travel", "adventure", "landscape"],
        "food": ["food", "cooking", "restaurant"],
        "technology": ["technology", "computer", "future"],
        "nature": ["nature", "forest", "ocean"],
        "space": ["space", "galaxy", "stars"],
        "sports": ["sports", "athlete", "competition"],
        "music": ["music", "concert", "performance"],
        "city": ["city", "urban", "skyline"],
        "animals": ["animals", "wildlife", "nature"],
    }
    
    for key, values in keyword_map.items():
        if key in text or any(v in text for v in values):
            keywords.extend(values[:2])
    
    if not keywords:
        keywords = ["abstract", "motion", "colorful"]
    
    # Check cache first
    query = random.choice(keywords)
    cache_path = BROLL_DIR / f"{query.replace(' ', '_')}.mp4"
    
    if cache_path.exists():
        return str(cache_path)
    
    # Download new video
    if download_pexels_video(query, str(cache_path)):
        return str(cache_path)
    
    # Fallback to existing backgrounds
    bg_files = list(BACKGROUNDS_DIR.glob("*.mp4"))
    if bg_files:
        return str(random.choice(bg_files))
    
    return None


async def generate_voiceover_v2(text: str, output_path: str, 
                                 voice: str = None, retries: int = 5) -> float:
    """Generate ENGAGING voiceover with dynamic voice and style. Includes fallback."""
    if voice is None:
        voice = random.choice(VOICES)
    
    last_error = None
    
    # Try different voices if one fails (Edge-TTS rate limiting)
    voices_to_try = [voice] + [v for v in VOICES if v != voice][:2]
    
    for voice_attempt in voices_to_try:
        for attempt in range(retries):
            try:
                # Simpler settings - avoid rate limits
                rate = "+0%" if attempt > 1 else "-3%"  # Use default on retries
                pitch = "+0Hz" if attempt > 1 else "+5Hz"  # Use default on retries
                
                # Create communicate object - use minimal params on retries
                if attempt <= 1:
                    communicate = edge_tts.Communicate(
                        text, 
                        voice_attempt,
                        rate=rate,
                        pitch=pitch
                    )
                else:
                    # Minimal params on later retries
                    communicate = edge_tts.Communicate(text, voice_attempt)
                
                await communicate.save(output_path)
                
                # Get duration
                audio = AudioFileClip(output_path)
                duration = audio.duration
                audio.close()
                
                print(f"   ✅ TTS success with {voice_attempt}")
                return duration
                
            except Exception as e:
                last_error = e
                print(f"   ⚠️ TTS attempt {attempt + 1}/{retries} with {voice_attempt} failed: {e}")
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 45  # Longer wait (45s per retry)
                    print(f"   Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        # If all retries with this voice failed, try next voice
        print(f"   ⚠️ All retries with {voice_attempt} failed, trying next voice...")
    
    # FALLBACK: Try gTTS (Google TTS) - more reliable but less engaging
    print("   🔄 Trying gTTS fallback...")
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        
        # Get duration
        audio = AudioFileClip(output_path)
        duration = audio.duration
        audio.close()
        
        print(f"   ✅ gTTS fallback success")
        return duration
    except Exception as gtts_error:
        print(f"   ⚠️ gTTS also failed: {gtts_error}")
    
    raise last_error if last_error else Exception("TTS generation failed after trying all options")


def pil_to_moviepy_clip(pil_image: Image.Image, duration: float) -> ImageClip:
    """Convert PIL Image to MoviePy ImageClip."""
    import numpy as np
    # Convert to RGB if RGBA
    if pil_image.mode == 'RGBA':
        # Create a composited version with transparency
        arr = np.array(pil_image)
        return ImageClip(arr).set_duration(duration)
    else:
        arr = np.array(pil_image)
        return ImageClip(arr).set_duration(duration)


def create_animated_vs(theme: VideoTheme, duration: float) -> VideoFileClip:
    """Create an animated VS badge that pulses."""
    frames = []
    fps = 30
    num_frames = int(duration * fps)
    
    for i in range(min(num_frames, 60)):  # Limit to 2 seconds of unique animation
        # Pulsing effect
        scale = 1.0 + 0.1 * math.sin(i * 0.3)
        size = int(120 * scale)
        
        vs_img = create_vs_badge(size, theme)
        frames.append(vs_img)
    
    # If we need more frames, repeat
    if num_frames > 60:
        frames = frames * (num_frames // 60 + 1)
    frames = frames[:num_frames]
    
    # Convert to video
    import numpy as np
    clips = []
    for i, frame in enumerate(frames):
        arr = np.array(frame)
        clip = ImageClip(arr).set_duration(1/fps).set_start(i/fps)
        clips.append(clip)
    
    return CompositeVideoClip(clips, size=(120, 120)).set_duration(duration)


async def generate_video_v2(question: dict, output_filename: str = None) -> str:
    """Generate a professional viral-quality video."""
    print("\n🎬 Starting PROFESSIONAL video generation (V2)...")
    
    # Select random theme
    theme = random.choice(list(THEMES.values()))
    print(f"🎨 Using theme: {theme.name}")
    
    # Extract question data
    option_a = question['option_a']
    option_b = question['option_b']
    percentage_a = question.get('percentage_a', random.randint(30, 70))
    percentage_b = 100 - percentage_a
    
    print(f"📝 Question: Would you rather...")
    print(f"   A: {option_a}")
    print(f"   B: {option_b}")
    
    # Hook phrases for visual display
    hooks = [
        "THIS IS IMPOSSIBLE!",
        "CHOOSE WISELY!",
        "NO ONE AGREES!",
        "THINK FAST!",
        "CAN'T DECIDE?",
    ]
    hook = random.choice(hooks)
    
    # Short voiceover (Edge-TTS has length limits)
    voiceover_templates = [
        f"Would you rather... {option_a}... OR... {option_b}? Comment your choice!",
        f"This is impossible! Would you rather... {option_a}... OR... {option_b}?",
        f"Choose wisely! Would you rather... {option_a}... OR... {option_b}?",
        f"Here's a tough one. Would you rather... {option_a}... OR... {option_b}?",
        f"No one can agree! Would you rather... {option_a}... OR... {option_b}?",
    ]
    
    voiceover_text = random.choice(voiceover_templates)
    
    # Generate voiceover
    voiceover_path = str(OUTPUT_DIR / "temp_voiceover.mp3")
    print("🎤 Generating voiceover...")
    voiceover_duration = await generate_voiceover_v2(voiceover_text, voiceover_path)
    print(f"   Duration: {voiceover_duration:.1f}s")
    
    # Load voiceover
    voiceover_audio = AudioFileClip(voiceover_path)
    
    # Calculate timeline
    intro_duration = 1.5  # Hook text
    question_start = intro_duration
    question_duration = voiceover_duration + 1
    countdown_start = question_start + question_duration
    countdown_duration = 4  # 3, 2, 1, reveal
    reveal_time = countdown_start + countdown_duration
    outro_duration = 3  # CTA
    total_duration = reveal_time + outro_duration
    
    print(f"⏱️ Total duration: {total_duration:.1f}s")
    
    # Get B-roll video
    print("📹 Getting background video...")
    broll_path = get_broll_for_question(question)
    
    if broll_path and os.path.exists(broll_path):
        try:
            bg_clip = VideoFileClip(broll_path)
            # Resize and crop to vertical
            bg_ratio = bg_clip.w / bg_clip.h
            target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
            
            if bg_ratio > target_ratio:
                new_height = VIDEO_HEIGHT
                new_width = int(VIDEO_HEIGHT * bg_ratio)
            else:
                new_width = VIDEO_WIDTH
                new_height = int(VIDEO_WIDTH / bg_ratio)
            
            bg_clip = bg_clip.resize((new_width, new_height))
            x_center = new_width // 2
            y_center = new_height // 2
            bg_clip = bg_clip.crop(x_center=x_center, y_center=y_center,
                                   width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
            
            # Loop if needed
            if bg_clip.duration < total_duration:
                n_loops = int(total_duration / bg_clip.duration) + 1
                bg_clip = bg_clip.loop(n=n_loops)
            bg_clip = bg_clip.subclip(0, total_duration)
            
            # Darken for text readability
            bg_clip = bg_clip.fx(vfx.colorx, 0.4)
        except Exception as e:
            print(f"   ⚠️ B-roll load failed: {e}, using gradient")
            bg_clip = None
    else:
        bg_clip = None
    
    # Create gradient background if no B-roll
    if bg_clip is None:
        gradient_img = create_gradient_background(
            VIDEO_WIDTH, VIDEO_HEIGHT,
            theme.gradient_start, theme.gradient_end
        )
        bg_clip = pil_to_moviepy_clip(gradient_img, total_duration)
    
    print("🎨 Creating visual elements...")
    
    # Create option panels
    panel_height = VIDEO_HEIGHT // 2 - 80
    
    panel_a_img = create_option_panel_image(
        VIDEO_WIDTH, panel_height,
        theme.option_a_gradient,
        option_a, "OPTION A",
        "top"
    )
    panel_a_clip = pil_to_moviepy_clip(panel_a_img, total_duration - intro_duration)
    panel_a_clip = panel_a_clip.set_position(('center', 0)).set_start(intro_duration)
    # Fade in
    panel_a_clip = panel_a_clip.crossfadein(0.5)
    
    panel_b_img = create_option_panel_image(
        VIDEO_WIDTH, panel_height,
        theme.option_b_gradient,
        option_b, "OPTION B",
        "bottom"
    )
    panel_b_clip = pil_to_moviepy_clip(panel_b_img, total_duration - intro_duration)
    panel_b_clip = panel_b_clip.set_position(('center', VIDEO_HEIGHT // 2 + 80)).set_start(intro_duration)
    panel_b_clip = panel_b_clip.crossfadein(0.5)
    
    # Create VS badge
    vs_img = create_vs_badge(140, theme)
    vs_clip = pil_to_moviepy_clip(vs_img, total_duration - intro_duration)
    vs_clip = vs_clip.set_position(('center', 'center')).set_start(intro_duration)
    
    # Create hook text
    hook_img = create_hook_text(VIDEO_WIDTH, VIDEO_HEIGHT, hook, theme)
    hook_clip = pil_to_moviepy_clip(hook_img, intro_duration)
    hook_clip = hook_clip.set_position(('center', 'center')).set_start(0)
    hook_clip = hook_clip.crossfadeout(0.3)
    
    # Create countdown clips
    countdown_clips = []
    for i, num in enumerate([3, 2, 1]):
        cd_img = create_countdown_frame(num, 200, theme)
        cd_clip = pil_to_moviepy_clip(cd_img, 1.0)
        cd_clip = cd_clip.set_position(('center', 'center'))
        cd_clip = cd_clip.set_start(countdown_start + i)
        cd_clip = cd_clip.crossfadein(0.1).crossfadeout(0.1)
        countdown_clips.append(cd_clip)
    
    # Create percentage reveal
    reveal_img = create_percentage_reveal_frame(
        percentage_a, percentage_b,
        VIDEO_WIDTH, VIDEO_HEIGHT,
        theme
    )
    reveal_clip = pil_to_moviepy_clip(reveal_img, outro_duration + 1)
    reveal_clip = reveal_clip.set_position(('center', 'center'))
    reveal_clip = reveal_clip.set_start(reveal_time)
    reveal_clip = reveal_clip.crossfadein(0.3)
    
    # Create CTA
    cta_img = create_cta_text(VIDEO_WIDTH, VIDEO_HEIGHT, theme)
    cta_clip = pil_to_moviepy_clip(cta_img, outro_duration)
    cta_clip = cta_clip.set_position(('center', 'center'))
    cta_clip = cta_clip.set_start(reveal_time + 1)
    cta_clip = cta_clip.crossfadein(0.3)
    
    print("🎥 Compositing video...")
    
    # Composite all layers
    all_clips = [
        bg_clip,
        hook_clip,
        panel_a_clip,
        panel_b_clip,
        vs_clip,
        *countdown_clips,
        reveal_clip,
        cta_clip
    ]
    
    final_video = CompositeVideoClip(all_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    final_video = final_video.set_duration(total_duration)
    
    # Get background music (mild, appropriate for content)
    print("🎵 Getting background music...")
    audio_clips = [voiceover_audio.set_start(intro_duration + 0.5)]
    
    try:
        from background_music import get_background_music, get_mood_for_question
        music_mood = get_mood_for_question(option_a, option_b)
        music_path = get_background_music(music_mood, total_duration)
        
        if music_path and os.path.exists(music_path):
            music_clip = AudioFileClip(music_path)
            # Loop if shorter than video
            if music_clip.duration < total_duration:
                music_clip = music_clip.fx(vfx.loop, duration=total_duration)
            else:
                music_clip = music_clip.subclip(0, total_duration)
            
            # Set music to LOW volume (15% - mild background)
            music_clip = music_clip.volumex(0.15)
            audio_clips.append(music_clip.set_start(0))
            print(f"   ✅ Added background music: {music_mood} mood")
        else:
            print("   ⚠️ No background music available")
    except Exception as e:
        print(f"   ⚠️ Music error: {e}")
    
    # Combine audio
    final_audio = CompositeAudioClip(audio_clips)
    final_video = final_video.set_audio(final_audio)
    
    # Generate output filename
    if output_filename is None:
        hash_input = f"{option_a}{option_b}{time.time()}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        output_filename = f"wyr_v2_{short_hash}.mp4"
    
    output_path = OUTPUT_DIR / output_filename
    
    print(f"🎥 Rendering to {output_path}...")
    
    # HIGH QUALITY export settings (from YShortsGen)
    try:
        final_video.write_videofile(
            str(output_path),
            fps=VIDEO_FPS,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='12000k',  # High quality bitrate
            audio_bitrate='256k',  # Better audio
            ffmpeg_params=['-crf', '20', '-pix_fmt', 'yuv420p'],  # Quality settings
            threads=4,
            logger='bar' if sys.stdout.isatty() else None
        )
    except Exception as e:
        print(f"⚠️ High-quality export failed, trying fallback: {e}")
        final_video.write_videofile(
            str(output_path),
            fps=VIDEO_FPS,
            codec='libx264',
            audio_codec='aac',
            preset='fast',
            bitrate='6000k',
            threads=4,
            logger=None
        )
    
    # Cleanup
    if os.path.exists(voiceover_path):
        os.remove(voiceover_path)
    
    final_video.close()
    if bg_clip:
        bg_clip.close()
    voiceover_audio.close()
    
    print(f"\n✅ PROFESSIONAL video generated!")
    print(f"📁 Output: {output_path}")
    print(f"🎨 Theme: {theme.name}")
    print(f"⏱️ Duration: {total_duration:.1f}s")
    
    return str(output_path)


async def generate_and_upload_v2(count: int = 1, upload: bool = True):
    """Generate professional videos and optionally upload."""
    print(f"\n🚀 Generating {count} PROFESSIONAL video(s)...")
    
    ensure_directories()
    
    # Load questions
    if not QUESTIONS_FILE.exists():
        print("❌ No questions.json found!")
        return []
    
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    random.shuffle(questions)
    selected = questions[:count]
    
    results = []
    for i, question in enumerate(selected, 1):
        print(f"\n{'='*60}")
        print(f"📹 Video {i}/{count}")
        print(f"{'='*60}")
        
        try:
            video_path = await generate_video_v2(question)
            
            if upload and video_path:
                try:
                    from youtube_uploader import upload_quiz_video
                    print("\n📤 Uploading to YouTube...")
                    result = upload_quiz_video(video_path, question)
                    print(f"🎉 Video live at: {result.get('url', 'Unknown')}")
                    results.append({
                        'video': video_path,
                        'question': question,
                        'upload': result
                    })
                except Exception as e:
                    print(f"⚠️ Upload failed: {e}")
                    results.append({
                        'video': video_path,
                        'question': question,
                        'upload': None
                    })
            else:
                results.append({
                    'video': video_path,
                    'question': question,
                    'upload': None
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    uploaded = sum(1 for r in results if r.get('upload'))
    print(f"\n{'='*60}")
    print(f"📊 COMPLETE!")
    print(f"   Generated: {len(results)}/{count}")
    print(f"   Uploaded: {uploaded}/{len(results)}")
    print(f"{'='*60}")
    
    return results


def main():
    """Main entry point."""
    ensure_directories()
    
    if not QUESTIONS_FILE.exists():
        print("❌ Error: questions.json not found!")
        sys.exit(1)
    
    import argparse
    parser = argparse.ArgumentParser(description="QuizBot V2 - Professional Video Generator")
    parser.add_argument("--batch", "-b", type=int, default=1, help="Number of videos")
    parser.add_argument("--upload", "-u", action="store_true", help="Upload to YouTube")
    parser.add_argument("--no-upload", action="store_true", help="Don't upload")
    
    args = parser.parse_args()
    
    should_upload = args.upload or (os.environ.get('AUTO_UPLOAD', '').lower() == 'true')
    if args.no_upload:
        should_upload = False
    
    asyncio.run(generate_and_upload_v2(count=args.batch, upload=should_upload))


if __name__ == "__main__":
    main()




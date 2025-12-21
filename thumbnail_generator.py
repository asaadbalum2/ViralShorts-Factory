#!/usr/bin/env python3
"""
Thumbnail Generator for ViralShorts Factory v7.15
==================================================

Generates high-CTR thumbnails automatically:
- AI generates thumbnail text/concept
- High-contrast colors
- Clean, readable design
- Matches video content

FREE: Uses PIL (no paid services)
"""

import os
import random
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not available")
    Image = None


# Thumbnail settings
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# Color schemes that work for thumbnails (high contrast)
COLOR_SCHEMES = [
    {"bg": (30, 30, 30), "text": (255, 255, 0), "accent": (255, 50, 50)},  # Dark + Yellow
    {"bg": (20, 20, 80), "text": (255, 255, 255), "accent": (0, 255, 255)},  # Navy + White
    {"bg": (80, 20, 20), "text": (255, 255, 255), "accent": (255, 200, 0)},  # Dark Red + White
    {"bg": (20, 60, 20), "text": (255, 255, 255), "accent": (50, 255, 50)},  # Dark Green + White
    {"bg": (50, 0, 80), "text": (255, 255, 255), "accent": (255, 100, 255)},  # Purple + White
]


def get_thumbnail_font(size: int = 72) -> Optional[ImageFont.FreeTypeFont]:
    """Get a bold font for thumbnails."""
    font_paths = [
        "assets/fonts/bebas-neue.ttf",
        "assets/fonts/oswald-bold.ttf",
        "assets/fonts/anton.ttf",
        "assets/fonts/archivo-black.ttf",
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    
    try:
        return ImageFont.load_default()
    except:
        return None


def generate_thumbnail(
    topic: str,
    category: str = "",
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Generate a high-CTR thumbnail for a video.
    
    Args:
        topic: The video topic (used for thumbnail text)
        category: Optional category for color scheme selection
        output_path: Where to save (defaults to assets/thumbnails/)
    
    Returns:
        Path to generated thumbnail or None
    """
    if Image is None:
        print("PIL not available for thumbnail generation")
        return None
    
    # Create output directory
    thumb_dir = Path("assets/thumbnails")
    thumb_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_path:
        import hashlib
        hash_id = hashlib.md5(topic.encode()).hexdigest()[:8]
        output_path = str(thumb_dir / f"thumb_{hash_id}.png")
    
    # Select color scheme
    color_scheme = random.choice(COLOR_SCHEMES)
    
    # Create thumbnail
    img = Image.new('RGB', (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color_scheme["bg"])
    draw = ImageDraw.Draw(img)
    
    # Generate thumbnail text (shortened topic)
    thumb_text = shorten_for_thumbnail(topic)
    
    # Draw text
    font_large = get_thumbnail_font(96)
    font_medium = get_thumbnail_font(48)
    
    if not font_large:
        print("No font available for thumbnail")
        return None
    
    # Calculate text position (centered)
    words = thumb_text.upper().split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_text = " ".join(current_line)
        try:
            bbox = draw.textbbox((0, 0), test_text, font=font_large)
            if bbox[2] - bbox[0] > THUMBNAIL_WIDTH - 100:
                current_line.pop()
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        except:
            pass
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # Limit to 3 lines
    lines = lines[:3]
    
    # Draw each line centered
    line_height = 110
    total_height = len(lines) * line_height
    start_y = (THUMBNAIL_HEIGHT - total_height) // 2
    
    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=font_large)
            text_width = bbox[2] - bbox[0]
            x = (THUMBNAIL_WIDTH - text_width) // 2
            y = start_y + i * line_height
            
            # Draw outline
            for ox in range(-4, 5, 2):
                for oy in range(-4, 5, 2):
                    draw.text((x + ox, y + oy), line, fill=(0, 0, 0), font=font_large)
            
            # Draw main text
            draw.text((x, y), line, fill=color_scheme["text"], font=font_large)
        except Exception as e:
            print(f"Text drawing error: {e}")
    
    # Add category badge (optional)
    if category and font_medium:
        badge_text = category.upper()
        try:
            badge_bbox = draw.textbbox((0, 0), badge_text, font=font_medium)
            badge_width = badge_bbox[2] - badge_bbox[0] + 40
            badge_height = 60
            
            # Draw badge background
            badge_x = 40
            badge_y = THUMBNAIL_HEIGHT - badge_height - 40
            draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
                radius=10,
                fill=color_scheme["accent"]
            )
            
            # Draw badge text
            draw.text(
                (badge_x + 20, badge_y + 8),
                badge_text,
                fill=(0, 0, 0),
                font=font_medium
            )
        except:
            pass
    
    # Save
    try:
        img.save(output_path, "PNG", quality=95)
        print(f"   [OK] Thumbnail saved: {output_path}")
        return output_path
    except Exception as e:
        print(f"   [!] Thumbnail save failed: {e}")
        return None


def shorten_for_thumbnail(text: str, max_words: int = 6) -> str:
    """
    Shorten text for thumbnail display.
    Keep only the most impactful words.
    """
    # Remove common filler words
    skip_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 
                  'would', 'could', 'should', 'may', 'might', 'can', 'this',
                  'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
                  'we', 'they', 'what', 'which', 'who', 'whom', 'when',
                  'where', 'why', 'how', 'of', 'for', 'to', 'in', 'on', 'at'}
    
    words = text.split()
    important_words = [w for w in words if w.lower() not in skip_words]
    
    if len(important_words) > max_words:
        important_words = important_words[:max_words]
    
    # If too short, use original
    if len(important_words) < 2:
        return " ".join(words[:max_words])
    
    return " ".join(important_words)


if __name__ == "__main__":
    # Test thumbnail generation
    test_topics = [
        "Why Most People Will Never Be Rich",
        "The 5 Second Rule Changed My Life",
        "Your Brain is Lying to You",
    ]
    
    for topic in test_topics:
        print(f"\nGenerating thumbnail for: {topic}")
        result = generate_thumbnail(topic, "Psychology")
        print(f"Result: {result}")


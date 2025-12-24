#!/usr/bin/env python3
"""
CRITICAL FIXES for Video Quality Issues
========================================

This module provides REAL fixes that ENFORCE quality:
1. AI-driven font selection with ACTUAL application
2. Varied sound effects (not same pattern every time)
3. Minimum quality score enforcement (8+/10)
4. Numbered promise validation in CODE (not just prompts)
"""

import random
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# ============================================
# FIX 1: AI-DRIVEN FONT SELECTION
# ============================================

# Available fonts with their characteristics
AVAILABLE_FONTS = {
    "bebas-neue": {
        "moods": ["energetic", "bold", "action", "tech"],
        "categories": ["crypto", "tech", "fitness", "gaming"],
    },
    "oswald-bold": {
        "moods": ["professional", "serious", "news"],
        "categories": ["business", "news", "education"],
    },
    "anton": {
        "moods": ["dramatic", "impactful", "urgent"],
        "categories": ["breaking", "shocking", "trending"],
    },
    "montserrat-bold": {
        "moods": ["modern", "clean", "minimal"],
        "categories": ["lifestyle", "beauty", "fashion"],
    },
    "poppins-bold": {
        "moods": ["friendly", "approachable", "casual"],
        "categories": ["self_improvement", "mental_health", "productivity"],
    },
    "bangers": {
        "moods": ["fun", "playful", "exciting"],
        "categories": ["entertainment", "memes", "challenges"],
    },
    "permanent-marker": {
        "moods": ["personal", "authentic", "raw"],
        "categories": ["stories", "confessions", "tips"],
    },
    "archivo-black": {
        "moods": ["powerful", "statement", "bold"],
        "categories": ["motivation", "sports", "finance"],
    },
}


def select_font_for_content(category: str, mood: str = None, topic: str = None) -> str:
    """
    Select the BEST font based on content characteristics.
    This is NOT random - it's intelligent selection.
    
    Returns the font key to use.
    """
    category = category.lower() if category else "general"
    mood = mood.lower() if mood else "neutral"
    
    # Score each font based on match
    scores = {}
    for font_key, font_data in AVAILABLE_FONTS.items():
        score = 0
        
        # Category match (high weight)
        for cat in font_data["categories"]:
            if cat in category or category in cat:
                score += 10
        
        # Mood match (medium weight)
        for m in font_data["moods"]:
            if m in mood or mood in m:
                score += 5
        
        # Topic keyword match (low weight)
        if topic:
            topic_lower = topic.lower()
            for cat in font_data["categories"]:
                if cat in topic_lower:
                    score += 3
        
        scores[font_key] = score
    
    # Get best match (or random from top 3 if tie)
    max_score = max(scores.values())
    
    if max_score > 0:
        top_fonts = [k for k, v in scores.items() if v == max_score]
        return random.choice(top_fonts)
    else:
        # No specific match - use category-appropriate defaults
        category_defaults = {
            "tech": "bebas-neue",
            "crypto": "bebas-neue",
            "finance": "archivo-black",
            "self_improvement": "poppins-bold",
            "productivity": "poppins-bold",
            "mental_health": "poppins-bold",
            "entertainment": "bangers",
            "news": "oswald-bold",
        }
        
        for key, font in category_defaults.items():
            if key in category:
                return font
        
        # Ultimate fallback - random from all
        return random.choice(list(AVAILABLE_FONTS.keys()))


# ============================================
# FIX 2: VARIED SOUND EFFECTS
# ============================================

# SFX pools for different purposes
SFX_POOLS = {
    "hook": ["hit", "whoosh", "ding"],  # Variety for hooks
    "transition": ["whoosh", "tick", None],  # Some transitions silent
    "payoff": ["ding", "hit", None],  # Vary endings too
    "emphasis": ["tick", "ding", None],  # For emphasis moments
}


def get_varied_sfx_for_phrase(phrase_index: int, total_phrases: int, video_id: int = None) -> Optional[str]:
    """
    Get varied sound effect - NOT the same pattern every time.
    Uses video_id as seed for per-video consistency but cross-video variety.
    
    IMPROVED: More balanced weights for TRUE variety across videos.
    """
    # Use video ID to seed randomness for this video
    if video_id:
        random.seed(video_id + phrase_index * 7)  # Multiply by prime for better distribution
    
    if phrase_index == 0:
        # Hook: More balanced - 40% hit, 30% whoosh, 15% ding, 15% silent
        sfx = random.choices(
            ["hit", "whoosh", "ding", None],
            weights=[40, 30, 15, 15]
        )[0]
    elif phrase_index == total_phrases - 1:
        # Payoff: More balanced - 35% ding, 25% hit, 25% whoosh, 15% silent
        sfx = random.choices(
            ["ding", "hit", "whoosh", None],
            weights=[35, 25, 25, 15]
        )[0]
    else:
        # Middle phrases: More balanced - 30% whoosh, 25% tick, 25% silent, 20% ding
        sfx = random.choices(
            ["whoosh", "tick", None, "ding"],
            weights=[30, 25, 25, 20]
        )[0]
    
    # Reset random state
    random.seed()
    
    return sfx


# ============================================
# FIX 3: MINIMUM QUALITY ENFORCEMENT
# ============================================

MINIMUM_ACCEPTABLE_SCORE = 8
MAX_REGENERATION_ATTEMPTS = 3


def enforce_quality_score(content: Dict, ai_func, regenerate_func) -> Tuple[Dict, int]:
    """
    Enforce minimum quality score with regeneration.
    
    Returns (content, final_score)
    """
    score = content.get('evaluation_score', 0)
    
    if score >= MINIMUM_ACCEPTABLE_SCORE:
        return content, score
    
    # Need to regenerate
    for attempt in range(MAX_REGENERATION_ATTEMPTS):
        print(f"   [QUALITY] Score {score}/10 too low (min: {MINIMUM_ACCEPTABLE_SCORE}), regenerating (attempt {attempt + 1})...")
        
        # Regenerate with feedback
        feedback = f"Previous attempt scored {score}/10. Make it more engaging, specific, and valuable. Minimum acceptable is {MINIMUM_ACCEPTABLE_SCORE}/10."
        
        try:
            new_content = regenerate_func(feedback)
            if new_content:
                new_score = new_content.get('evaluation_score', 0)
                if new_score >= MINIMUM_ACCEPTABLE_SCORE:
                    print(f"   [QUALITY] Improved to {new_score}/10 - ACCEPTED")
                    return new_content, new_score
                score = new_score
                content = new_content
        except Exception as e:
            print(f"   [QUALITY] Regeneration failed: {e}")
    
    # After all attempts, accept best we have but log warning
    print(f"   [QUALITY WARNING] Could not achieve {MINIMUM_ACCEPTABLE_SCORE}/10 after {MAX_REGENERATION_ATTEMPTS} attempts. Best: {score}/10")
    return content, score


# ============================================
# FIX 4: NUMBERED PROMISE VALIDATION
# ============================================

def extract_promised_count(text: str) -> Optional[int]:
    """
    Extract any promised count from text.
    "5 tips" → 5
    "Here are 7 ways" → 7
    "Top 10 secrets" → 10
    """
    patterns = [
        r'(\d+)\s+(?:tips?|ways?|tricks?|secrets?|habits?|things?|facts?|signs?|reasons?|steps?|methods?)',
        r'(?:top|best|here are|these)\s+(\d+)',
        r'(\d+)\s+(?:of|that|which|to)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def count_items_in_content(phrases: List[str]) -> int:
    """
    Count actual items delivered in content.
    Looks for numbering patterns, bullet points, or distinct items.
    """
    item_count = 0
    
    for phrase in phrases:
        # Check for explicit numbering
        if re.match(r'^\s*\d+[\.\):]', phrase):
            item_count += 1
        # Check for "first", "second", etc.
        elif re.search(r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b', phrase, re.IGNORECASE):
            item_count += 1
        # Check for "one is", "another is", etc.
        elif re.search(r'\b(one is|another is|next is|also|finally)\b', phrase, re.IGNORECASE):
            item_count += 1
    
    return max(item_count, len(phrases) - 1)  # At minimum, each phrase after hook is an item


def validate_numbered_promise(hook: str, phrases: List[str]) -> Dict:
    """
    Validate that numbered promises are kept.
    
    Returns:
        {
            "promised": int or None,
            "delivered": int,
            "valid": bool,
            "fix_suggestion": str or None
        }
    """
    promised = extract_promised_count(hook)
    
    if promised is None:
        return {"promised": None, "delivered": None, "valid": True, "fix_suggestion": None}
    
    delivered = count_items_in_content(phrases[1:])  # Exclude hook
    
    if delivered >= promised:
        return {
            "promised": promised,
            "delivered": delivered,
            "valid": True,
            "fix_suggestion": None
        }
    else:
        # Promise broken!
        fix = f"Change '{promised}' to '{delivered}' in hook, or add {promised - delivered} more items to content"
        return {
            "promised": promised,
            "delivered": delivered,
            "valid": False,
            "fix_suggestion": fix
        }


def fix_broken_promise(hook: str, delivered_count: int) -> str:
    """
    Fix a hook with broken promise by changing the number.
    """
    patterns = [
        (r'(\d+)\s+(tips?|ways?|tricks?|secrets?|habits?|things?|facts?|signs?|reasons?|steps?|methods?)', 
         f'{delivered_count} \\2'),
        (r'(top|best|here are|these)\s+(\d+)', 
         f'\\1 {delivered_count}'),
    ]
    
    fixed_hook = hook
    for pattern, replacement in patterns:
        fixed_hook = re.sub(pattern, replacement, fixed_hook, flags=re.IGNORECASE)
    
    return fixed_hook


# ============================================
# FIX 5: CONTENT PROMPT CONSTRAINTS
# ============================================

CONTENT_CONSTRAINTS = """
=== CRITICAL RENDERING CONSTRAINTS ===
When generating content, you MUST know:

AVAILABLE FONTS (choose one that matches mood):
- bebas-neue: Bold, energetic (tech, crypto, fitness)
- oswald-bold: Professional, serious (business, news)
- anton: Dramatic, impactful (breaking news, shocking)
- montserrat-bold: Modern, clean (lifestyle, beauty)
- poppins-bold: Friendly, approachable (self-improvement, mental health)
- bangers: Fun, playful (entertainment, memes)
- permanent-marker: Personal, authentic (stories, tips)
- archivo-black: Powerful, statement (motivation, finance)

SOUND EFFECTS AVAILABLE:
- hit: Dramatic impact (for hooks)
- whoosh: Smooth transition
- ding: Positive reveal/payoff
- tick: Countdown/emphasis

NUMBERED PROMISES:
If you promise "X things" in the hook, you MUST deliver EXACTLY X items.
Each item must be clearly identifiable in a separate phrase.

OUTPUT FORMAT:
Your JSON must include:
{
  "font_choice": "font-key-from-above",
  "sfx_style": "dramatic|subtle|minimal",
  "promised_count": number or null,
  "items": [list of exactly promised_count items if applicable]
}
"""


def get_constraint_aware_prompt(base_prompt: str) -> str:
    """
    Inject constraints into any prompt to make AI aware of rendering limitations.
    """
    return f"{base_prompt}\n\n{CONTENT_CONSTRAINTS}"


# ============================================
# INTEGRATION HELPER
# ============================================

def apply_all_critical_fixes(
    content: Dict,
    category: str,
    topic: str,
    video_id: int = None
) -> Dict:
    """
    Apply all critical fixes to content before rendering.
    
    This should be called AFTER AI generation but BEFORE rendering.
    """
    fixed_content = content.copy()
    
    # 1. Select appropriate font
    mood = content.get('mood', content.get('music_mood', 'neutral'))
    font = select_font_for_content(category, mood, topic)
    fixed_content['selected_font'] = font
    print(f"   [FIX] Font selected: {font} (based on {category}/{mood})")
    
    # 2. Plan varied SFX
    phrases = content.get('phrases', [])
    sfx_plan = []
    for i in range(len(phrases)):
        sfx = get_varied_sfx_for_phrase(i, len(phrases), video_id)
        sfx_plan.append(sfx)
    fixed_content['sfx_plan'] = sfx_plan
    sfx_summary = [s for s in sfx_plan if s]
    print(f"   [FIX] SFX plan: {sfx_summary}")
    
    # 3. Validate numbered promise
    if phrases:
        validation = validate_numbered_promise(phrases[0], phrases)
        if not validation['valid']:
            print(f"   [FIX] Promise broken! Promised {validation['promised']}, delivered {validation['delivered']}")
            # Fix the hook
            fixed_hook = fix_broken_promise(phrases[0], validation['delivered'])
            fixed_content['phrases'][0] = fixed_hook
            fixed_content['promise_fixed'] = True
            print(f"   [FIX] Hook fixed: {fixed_hook[:50]}...")
        else:
            fixed_content['promise_fixed'] = False
    
    return fixed_content


if __name__ == "__main__":
    # Test the fixes
    print("Testing Critical Fixes...")
    
    # Test font selection
    font = select_font_for_content("self_improvement", "friendly", "Morning Habits")
    print(f"Font for self_improvement/friendly: {font}")
    
    # Test SFX variety
    print("\nSFX patterns for 3 different videos:")
    for vid in [12345, 67890, 11111]:
        pattern = [get_varied_sfx_for_phrase(i, 4, vid) for i in range(4)]
        print(f"  Video {vid}: {pattern}")
    
    # Test promise validation
    hook = "Here are 5 morning habits that will change your life"
    phrases = [hook, "First tip", "Second tip", "Third tip"]  # Only 3 items!
    result = validate_numbered_promise(hook, phrases)
    print(f"\nPromise validation: {result}")
    if not result['valid']:
        fixed = fix_broken_promise(hook, result['delivered'])
        print(f"Fixed hook: {fixed}")



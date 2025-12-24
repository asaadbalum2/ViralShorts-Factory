#!/usr/bin/env python3
"""
ViralShorts Factory - Ultimate Enhancements Module v12.0
=========================================================

BATCH 1: HUMAN FEEL (~60 enhancements)
- Category A: Anti-AI Detection (#90-109)
- Category B: Typography & Text (#110-129)
- Category C: Voice & Audio (#130-149)

Goal: Make videos INDISTINGUISHABLE from human-created content.

All enhancements are:
- AI-driven via generic master prompts
- 100% free (no paid APIs)
- Quota-aware (Groq for critical, Gemini for bulk)
- Fully autonomous
- Persistent learning via GitHub Artifacts
"""

import json
import os
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# State directory
STATE_DIR = Path("data/persistent")
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Import AI caller from v9
try:
    from enhancements_v9 import get_ai_caller, SmartAICaller
except ImportError:
    get_ai_caller = None
    SmartAICaller = None


# #############################################################################
# CATEGORY A: ANTI-AI DETECTION (#90-109)
# Make content feel genuinely human, not AI-generated
# #############################################################################

class NaturalSpeechRhythm:
    """
    #90: Varies sentence length and structure to feel natural.
    AI-generated content often has uniform sentence lengths.
    """
    
    RHYTHM_FILE = STATE_DIR / "natural_speech_rhythm.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.RHYTHM_FILE.exists():
                with open(self.RHYTHM_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "patterns": {
                "short_long_short": {"uses": 0, "engagement": 0},
                "building": {"uses": 0, "engagement": 0},
                "punchy": {"uses": 0, "engagement": 0},
                "conversational": {"uses": 0, "engagement": 0}
            },
            "best_pattern": "conversational"
        }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.RHYTHM_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_rhythm_instruction(self) -> str:
        """Get instruction for AI to vary sentence rhythm."""
        return """
SENTENCE RHYTHM (Anti-AI):
- Vary sentence lengths: Short. Then a longer one to explain. Short again.
- Mix: Simple sentences with complex, multi-clause ones.
- Use fragments occasionally. Like this. For emphasis.
- Average 8-15 words per sentence, but range from 3 to 25.
- Never have 3+ sentences of similar length in a row.
"""


class FillerWordInjector:
    """
    #91: Injects natural filler words to sound human.
    "You know", "actually", "here's the thing", etc.
    """
    
    FILLER_FILE = STATE_DIR / "filler_words.json"
    
    FILLER_WORDS = [
        "you know",
        "actually",
        "here's the thing",
        "look",
        "honestly",
        "basically",
        "I mean",
        "the thing is",
        "so",
        "right",
        "okay so",
        "now",
        "listen"
    ]
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.FILLER_FILE.exists():
                with open(self.FILLER_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"usage": {f: 0 for f in self.FILLER_WORDS}, "performance": {}}
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.FILLER_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_filler_instruction(self) -> str:
        """Get instruction for natural filler words."""
        return """
FILLER WORDS (Sound Human):
- Add 1-2 natural fillers per 30 seconds of content
- Options: "you know", "actually", "here's the thing", "look", "honestly"
- Place at: start of new thoughts, before important points, transitions
- DON'T overuse - max 3 per video
- Make them feel natural, not forced
"""
    
    def get_random_filler(self) -> str:
        return random.choice(self.FILLER_WORDS)


class BreathingPauseSimulator:
    """
    #92: Adds natural breathing pauses to script.
    Humans pause to breathe; AI doesn't.
    """
    
    def get_pause_instruction(self) -> str:
        return """
BREATHING PAUSES (Natural Feel):
- Insert [PAUSE] markers every 15-20 words
- Longer pause after important revelations
- Quick pause before power words
- Natural pause at commas and periods
- Pause pattern: speak-breathe-speak, not monotone rush
"""
    
    def add_pauses_to_script(self, script: str) -> str:
        """Add pause markers to script."""
        words = script.split()
        result = []
        word_count = 0
        
        for word in words:
            result.append(word)
            word_count += 1
            
            # Add pause every 15-20 words randomly
            if word_count >= random.randint(15, 20):
                if word.endswith(('.', ',', '!', '?')):
                    result.append('[PAUSE]')
                    word_count = 0
        
        return ' '.join(result)


class SelfCorrectionSimulator:
    """
    #93: Adds self-correction patterns that humans naturally do.
    "Actually, let me put it this way..."
    """
    
    CORRECTIONS = [
        "Actually, let me rephrase that",
        "Wait, here's a better way to say it",
        "Or actually",
        "Let me put it differently",
        "What I mean is"
    ]
    
    def get_correction_instruction(self) -> str:
        return """
SELF-CORRECTION (Human Touch):
- Occasionally "correct" yourself mid-thought
- "Actually, let me rephrase that..."
- "Wait, here's a better way to explain it..."
- Use sparingly - once per video max
- Makes content feel unscripted and authentic
"""


class OpinionInjector:
    """
    #94: Injects personal opinions, not just facts.
    AI tends to be neutral; humans have opinions.
    """
    
    OPINION_PHRASES = [
        "I think",
        "In my experience",
        "What's interesting to me is",
        "Personally, I believe",
        "The way I see it",
        "Here's what I find fascinating"
    ]
    
    def get_opinion_instruction(self) -> str:
        return """
OPINION INJECTION (Personal Voice):
- Include 1-2 personal opinions, not just facts
- "I think this is actually the most important part..."
- "What fascinates me about this is..."
- "Personally, I believe..."
- Share your perspective, don't just inform
- Makes content feel like a person, not a textbook
"""


class ColloquialLanguageDetector:
    """
    #95: Ensures language is conversational, not formal.
    """
    
    FORMAL_TO_CASUAL = {
        "utilize": "use",
        "implement": "do",
        "therefore": "so",
        "however": "but",
        "additionally": "also",
        "furthermore": "plus",
        "commence": "start",
        "terminate": "end",
        "obtain": "get",
        "require": "need",
        "sufficient": "enough",
        "approximately": "about",
        "demonstrate": "show",
        "facilitate": "help",
        "endeavor": "try"
    }
    
    def get_casual_instruction(self) -> str:
        return """
CASUAL LANGUAGE (Not Corporate):
- Use everyday words, not fancy ones
- "use" not "utilize", "get" not "obtain"
- "so" not "therefore", "but" not "however"
- Write like you talk to a friend
- Contractions are good: "don't", "isn't", "you're"
- Avoid: "in order to", "it is important to note", "one must"
"""
    
    def make_casual(self, text: str) -> str:
        """Convert formal words to casual equivalents."""
        result = text
        for formal, casual in self.FORMAL_TO_CASUAL.items():
            result = re.sub(rf'\b{formal}\b', casual, result, flags=re.IGNORECASE)
        return result


class RhetoricalQuestionGenerator:
    """
    #96: Adds rhetorical questions for engagement.
    """
    
    QUESTION_STARTERS = [
        "Ever wondered why",
        "Have you ever noticed",
        "Think about it",
        "What if I told you",
        "Sound familiar",
        "Know what's crazy"
    ]
    
    def get_rhetorical_instruction(self) -> str:
        return """
RHETORICAL QUESTIONS (Engagement):
- Start sections with questions: "Ever wondered why...?"
- Insert mid-video: "Think about it..."
- Close points with: "Sound familiar?"
- Questions create mental engagement
- Viewer feels like a conversation, not a lecture
"""


class PersonalPerspectiveEnforcer:
    """
    #97: Ensures first-person perspective when appropriate.
    """
    
    def get_perspective_instruction(self) -> str:
        return """
PERSONAL PERSPECTIVE (I, You, We):
- Use "I" and "you" frequently
- "I discovered..." not "It was discovered..."
- "You probably..." not "One might..."
- "Let me show you..." not "It will be shown..."
- Creates connection between creator and viewer
- Avoid passive voice - be active and direct
"""


class HumorWitInjector:
    """
    #98: Adds appropriate humor and wit.
    """
    
    HUMOR_TYPES = [
        "self_deprecating",
        "observational",
        "unexpected_comparison",
        "understatement",
        "exaggeration_for_effect"
    ]
    
    def get_humor_instruction(self) -> str:
        return """
HUMOR & WIT (Personality):
- Add light humor where appropriate (1-2 per video)
- Self-deprecating: "I learned this the hard way..."
- Observational: "We've all done this, admit it..."
- Unexpected comparisons: "It's like trying to..."
- Don't force it - only if it fits naturally
- Humor makes content memorable and shareable
"""


class ImperfectionInjector:
    """
    #99: Adds subtle imperfections that make content human.
    """
    
    def get_imperfection_instruction(self) -> str:
        return """
IMPERFECTIONS (Authenticity):
- Occasional casual asides
- "By the way..." tangents
- Express genuine surprise: "Okay, this one shocked me too"
- Show enthusiasm: "This is actually my favorite part"
- Admit uncertainty where honest: "I'm not 100% sure, but..."
- Perfect = fake. Imperfect = human.
"""


class EmotionalInflectionGuide:
    """
    #100: Guides emotional variation in delivery.
    """
    
    EMOTIONS = {
        "excited": "Raise energy, faster pace, higher pitch",
        "serious": "Slower, deeper, more measured",
        "curious": "Questioning tone, pause before reveal",
        "surprised": "Genuine shock, pitch variation",
        "empathetic": "Warm, understanding, slower"
    }
    
    def get_emotion_instruction(self) -> str:
        return """
EMOTIONAL VARIATION (Not Monotone):
- Mark emotional shifts in script: [EXCITED], [SERIOUS], [CURIOUS]
- Hook = Intriguing/Curious
- Problem = Serious/Empathetic
- Solution = Excited/Hopeful
- Reveal = Surprised/Amazed
- CTA = Warm/Inviting
- Emotion makes content memorable
"""


class StorytellingStructure:
    """
    #101: Structures content as stories, not lectures.
    """
    
    def get_story_instruction(self) -> str:
        return """
STORYTELLING (Not Lecturing):
- Frame facts as discoveries: "Here's what they found..."
- Use narrative tension: "But then something unexpected..."
- Include journey: "I used to think X, until..."
- Characters when possible: "Scientists at MIT..."
- Conflict and resolution: "The problem was... until..."
- Stories are remembered 22x better than facts
"""


class AnecdoteGenerator:
    """
    #102: Generates/suggests relevant anecdotes.
    """
    
    def get_anecdote_instruction(self) -> str:
        return """
ANECDOTES (Personal Stories):
- Include brief personal touches: "I remember when..."
- Relatable scenarios: "Picture this..."
- Third-party stories: "A friend of mine..."
- Real examples: "Last week, I saw..."
- Keep anecdotes SHORT - 1-2 sentences
- They humanize and prove points
"""


class RepetitionForEmphasis:
    """
    #103: Uses strategic repetition like humans do.
    """
    
    def get_repetition_instruction(self) -> str:
        return """
STRATEGIC REPETITION (Emphasis):
- Repeat key phrases for emphasis
- "This is important. Really important."
- "The secret is consistency. Consistency."
- Rule of three: "Faster, cheaper, better"
- Repetition = memorable
- But don't overdo - 1-2 uses per video
"""


class TransitionWordHumanizer:
    """
    #104: Uses natural transition words.
    """
    
    NATURAL_TRANSITIONS = [
        "Now here's the thing",
        "But wait",
        "So",
        "And get this",
        "Here's where it gets interesting",
        "The crazy part is",
        "Now",
        "Okay so",
        "But here's the twist"
    ]
    
    def get_transition_instruction(self) -> str:
        return """
NATURAL TRANSITIONS (Flow):
- Use casual transitions: "Now here's the thing..."
- "But wait, it gets better..."
- "And get this..."
- "Here's where it gets interesting..."
- Avoid: "Furthermore", "Moreover", "In addition"
- Transitions should feel like natural speech
"""


class ContractionsEnforcer:
    """
    #105: Ensures use of contractions (natural speech).
    """
    
    EXPANSIONS_TO_CONTRACTIONS = {
        "do not": "don't",
        "does not": "doesn't",
        "did not": "didn't",
        "is not": "isn't",
        "are not": "aren't",
        "was not": "wasn't",
        "were not": "weren't",
        "have not": "haven't",
        "has not": "hasn't",
        "will not": "won't",
        "would not": "wouldn't",
        "could not": "couldn't",
        "should not": "shouldn't",
        "cannot": "can't",
        "it is": "it's",
        "that is": "that's",
        "what is": "what's",
        "here is": "here's",
        "there is": "there's",
        "you are": "you're",
        "we are": "we're",
        "they are": "they're",
        "I am": "I'm",
        "I have": "I've",
        "I will": "I'll",
        "you will": "you'll",
        "we will": "we'll",
        "let us": "let's"
    }
    
    def apply_contractions(self, text: str) -> str:
        """Convert formal expansions to contractions."""
        result = text
        for expansion, contraction in self.EXPANSIONS_TO_CONTRACTIONS.items():
            result = re.sub(rf'\b{expansion}\b', contraction, result, flags=re.IGNORECASE)
        return result


class DirectAddressEnforcer:
    """
    #106: Ensures direct address to viewer ("you").
    """
    
    def get_direct_address_instruction(self) -> str:
        return """
DIRECT ADDRESS (Talk TO them):
- Use "you" frequently - at least once per 10 seconds
- "You need to know this"
- "What you might not realize"
- "Here's what happens to you"
- Avoid "one", "people", "viewers"
- They should feel you're talking TO them, not ABOUT them
"""


class ConfidenceCalibrator:
    """
    #107: Calibrates confidence level to sound authentic.
    """
    
    def get_confidence_instruction(self) -> str:
        return """
CONFIDENCE CALIBRATION:
- Strong claims: "This absolutely works"
- Honest hedging: "In most cases..." 
- Show expertise: "What I've found is..."
- Admit limits: "This depends on..."
- Over-confidence = fake
- Under-confidence = weak
- Balance = trustworthy
"""


class EnthusiasmAuthenticator:
    """
    #108: Makes enthusiasm feel genuine, not fake.
    """
    
    def get_enthusiasm_instruction(self) -> str:
        return """
GENUINE ENTHUSIASM (Not Fake Hype):
- Show excitement about specific things, not everything
- "This next part is actually my favorite"
- Explain WHY you're excited: "What's cool about this is..."
- Calm enthusiasm > fake hype
- Vary energy - not everything is "AMAZING!"
- Genuine > Performative
"""


class VulnerabilityInjector:
    """
    #109: Adds appropriate vulnerability/honesty.
    """
    
    def get_vulnerability_instruction(self) -> str:
        return """
VULNERABILITY (Trust Building):
- Admit past mistakes: "I used to get this wrong too"
- Share struggles: "This took me forever to figure out"
- Be honest: "Not gonna lie, this is hard"
- Show learning journey: "What finally clicked for me..."
- Vulnerability = Relatability = Trust
- Don't be perfect - be real
"""


# Master function to get all Anti-AI instructions
def get_anti_ai_master_prompt() -> str:
    """Returns comprehensive prompt for human-like content."""
    return """
# ANTI-AI CONTENT GUIDELINES
Your goal: Create content INDISTINGUISHABLE from a real human creator.

## SPEECH PATTERNS
- Vary sentence length: Short. Then longer explanations. Punchy again.
- Use contractions: "don't", "it's", "you're" - never formal expansions
- Add natural fillers (sparingly): "you know", "actually", "here's the thing"
- Include breathing pauses - humans need to breathe

## PERSONAL VOICE
- Use "I" and "you" - this is a conversation, not a lecture
- Share opinions: "I think...", "What fascinates me..."
- Add light humor where natural
- Express genuine enthusiasm for specific parts
- Admit uncertainty when honest: "I'm not 100% sure, but..."

## AUTHENTICITY SIGNALS
- Self-correct occasionally: "Actually, let me rephrase that..."
- Show your journey: "I used to think X, until..."
- Be vulnerable: "This took me forever to figure out"
- Use casual language: "use" not "utilize", "so" not "therefore"

## STORYTELLING
- Frame facts as discoveries
- Use narrative tension
- Include brief anecdotes
- Make it a journey, not a list

## EMOTIONAL VARIATION
- Hook = Intriguing
- Problem = Serious
- Solution = Excited
- Reveal = Surprised
- CTA = Warm

Remember: Perfect = Fake. Human = Imperfect but genuine.
"""


# #############################################################################
# CATEGORY B: TYPOGRAPHY & TEXT (#110-129)
# Professional text, subtitles, and on-screen elements
# #############################################################################

class FontPsychologyOptimizer:
    """
    #110: Selects fonts based on psychological impact.
    Different fonts evoke different emotions.
    """
    
    FONT_FILE = STATE_DIR / "font_psychology.json"
    
    # Font categories and their psychological effects
    FONT_PSYCHOLOGY = {
        "bold_sans": {
            "fonts": ["Impact", "Arial Black", "Bebas Neue"],
            "emotions": ["power", "urgency", "modern", "confident"],
            "best_for": ["shocking_facts", "motivation", "warnings"]
        },
        "friendly_sans": {
            "fonts": ["Comic Sans", "Nunito", "Quicksand"],
            "emotions": ["friendly", "approachable", "casual"],
            "best_for": ["life_hacks", "fun_facts", "lifestyle"]
        },
        "elegant_serif": {
            "fonts": ["Playfair Display", "Georgia", "Times"],
            "emotions": ["trust", "authority", "classic"],
            "best_for": ["finance", "education", "history"]
        },
        "tech_mono": {
            "fonts": ["Roboto Mono", "Source Code Pro"],
            "emotions": ["tech", "modern", "precise"],
            "best_for": ["tech", "science", "data"]
        },
        "handwritten": {
            "fonts": ["Caveat", "Patrick Hand", "Indie Flower"],
            "emotions": ["personal", "authentic", "casual"],
            "best_for": ["stories", "personal", "advice"]
        }
    }
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.FONT_FILE.exists():
                with open(self.FONT_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"category_fonts": {}, "performance": {}}
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.FONT_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_recommended_font(self, category: str, mood: str) -> Dict:
        """Get recommended font based on category and mood."""
        # Map categories to font types
        category_map = {
            "psychology": "elegant_serif",
            "finance": "elegant_serif",
            "motivation": "bold_sans",
            "life_hacks": "friendly_sans",
            "tech": "tech_mono",
            "science": "tech_mono",
            "shocking_facts": "bold_sans",
            "personal": "handwritten"
        }
        
        font_type = category_map.get(category, "bold_sans")
        font_data = self.FONT_PSYCHOLOGY.get(font_type, self.FONT_PSYCHOLOGY["bold_sans"])
        
        return {
            "font_type": font_type,
            "recommended_fonts": font_data["fonts"],
            "emotions": font_data["emotions"]
        }


class DynamicFontSizer:
    """
    #111: Dynamically sizes text for emphasis.
    Important words = BIGGER.
    """
    
    def get_sizing_rules(self) -> Dict:
        return {
            "base_size": 60,  # Base font size
            "power_word_multiplier": 1.4,  # 40% bigger for power words
            "number_multiplier": 1.3,  # Numbers slightly bigger
            "whisper_multiplier": 0.8,  # Smaller for asides
            "max_size": 90,
            "min_size": 40
        }
    
    def get_sizing_instruction(self) -> str:
        return """
DYNAMIC TEXT SIZING:
- Power words (SECRET, NEVER, ALWAYS): 40% larger
- Numbers: 30% larger
- Whispered asides: 20% smaller
- Key phrases: LARGER
- Supporting text: smaller
- This guides viewer's eye to what matters
"""


class WordHighlightSynchronizer:
    """
    #112: Highlights words in sync with audio.
    Creates karaoke-style effect.
    """
    
    def get_highlight_instruction(self) -> str:
        return """
WORD HIGHLIGHTING (Sync with Audio):
- Highlight current word being spoken
- Use color change or underline
- Creates engagement and readability
- Helps with retention
- Essential for non-native speakers
"""


class ColorCodedEmphasis:
    """
    #113: Uses color to code meaning.
    Red = warning, Green = tip, Yellow = important.
    """
    
    COLOR_MEANINGS = {
        "warning": "#FF4444",  # Red
        "tip": "#44FF44",      # Green
        "important": "#FFDD44", # Yellow
        "question": "#44DDFF",  # Cyan
        "money": "#44FF44",     # Green
        "danger": "#FF4444",    # Red
        "benefit": "#44FF44",   # Green
        "problem": "#FF8844"    # Orange
    }
    
    def get_color_for_meaning(self, meaning: str) -> str:
        return self.COLOR_MEANINGS.get(meaning, "#FFFFFF")
    
    def get_color_instruction(self) -> str:
        return """
COLOR-CODED TEXT:
- Red/Orange: Warnings, problems, dangers
- Green: Tips, benefits, money savings
- Yellow: Important points, highlights
- Blue/Cyan: Questions, curiosity
- White: Normal content
- Use sparingly - max 2-3 colors per video
"""


class TextAnimationVariety:
    """
    #114: Varies text animations to prevent monotony.
    """
    
    ANIMATIONS = [
        "fade_in",
        "slide_up",
        "slide_left",
        "pop_in",
        "typewriter",
        "word_by_word",
        "bounce",
        "zoom_in"
    ]
    
    ANIMATION_FILE = STATE_DIR / "text_animations.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        try:
            if self.ANIMATION_FILE.exists():
                with open(self.ANIMATION_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"recent": [], "performance": {}}
    
    def _save(self):
        with open(self.ANIMATION_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_next_animation(self) -> str:
        """Get animation, avoiding recent repetition."""
        available = [a for a in self.ANIMATIONS if a not in self.data.get("recent", [])[-3:]]
        if not available:
            available = self.ANIMATIONS
        choice = random.choice(available)
        self.data.setdefault("recent", []).append(choice)
        self.data["recent"] = self.data["recent"][-10:]
        self._save()
        return choice


class MobileFirstTextPosition:
    """
    #115: Positions text optimally for mobile viewing.
    """
    
    SAFE_ZONES = {
        "top": {"y_start": 0.05, "y_end": 0.25},
        "center": {"y_start": 0.35, "y_end": 0.65},
        "bottom": {"y_start": 0.70, "y_end": 0.90}
    }
    
    def get_position_instruction(self) -> str:
        return """
MOBILE-FIRST TEXT POSITION:
- Keep text in center-bottom or center-top
- Avoid edges (gets cut off on some devices)
- Leave 10% margin from all sides
- Don't block faces or main action
- Bottom third = most common for captions
- Top = secondary info or category labels
"""


class ReadingSpeedOptimizer:
    """
    #116: Optimizes text display time for readability.
    """
    
    WORDS_PER_SECOND = 3  # Average reading speed
    MIN_DISPLAY_TIME = 1.5  # Minimum seconds on screen
    
    def calculate_display_time(self, text: str) -> float:
        """Calculate optimal display time for text."""
        word_count = len(text.split())
        reading_time = word_count / self.WORDS_PER_SECOND
        return max(reading_time, self.MIN_DISPLAY_TIME)
    
    def get_reading_instruction(self) -> str:
        return """
READING SPEED OPTIMIZATION:
- 3 words per second maximum
- Minimum 1.5 seconds on screen
- Longer sentences = longer display
- Important points = extra 0.5 seconds
- Don't rush - if they can't read it, it's useless
"""


class SubtitleStyleOptimizer:
    """
    #117: Optimizes subtitle styling for engagement.
    """
    
    SUBTITLE_STYLES = {
        "modern": {
            "font": "bold sans-serif",
            "size": "large",
            "shadow": True,
            "background": "semi-transparent"
        },
        "clean": {
            "font": "sans-serif",
            "size": "medium",
            "shadow": True,
            "background": None
        },
        "bold": {
            "font": "extra-bold",
            "size": "extra-large",
            "shadow": True,
            "background": None
        }
    }
    
    def get_style_instruction(self) -> str:
        return """
SUBTITLE STYLING:
- Bold, readable font (no thin fonts)
- Text shadow or outline for contrast
- Large enough for mobile (60px minimum)
- High contrast with background
- Consistent style throughout video
- Max 2 lines on screen at once
"""


class EmojiIntegration:
    """
    #118: Strategically integrates emojis.
    """
    
    CATEGORY_EMOJIS = {
        "money": ["💰", "💵", "📈", "🤑"],
        "psychology": ["🧠", "💭", "🤔", "💡"],
        "health": ["💪", "❤️", "🏃", "🥗"],
        "motivation": ["🔥", "💪", "⭐", "🚀"],
        "warning": ["⚠️", "🚨", "❌", "⛔"],
        "tip": ["✅", "💡", "👍", "✨"],
        "shocking": ["😱", "🤯", "😮", "❗"]
    }
    
    def get_emoji_instruction(self) -> str:
        return """
EMOJI INTEGRATION:
- Use sparingly: 1-3 per video
- Match category: 💰 for money, 🧠 for psychology
- Place at key moments, not randomly
- Add to important points: "✅ The key takeaway"
- Never overuse - it looks spammy
- Emojis draw the eye - use strategically
"""


class TextContrastOptimizer:
    """
    #119: Ensures text has proper contrast.
    """
    
    def get_contrast_instruction(self) -> str:
        return """
TEXT CONTRAST (Readability):
- Always use text shadow or stroke
- Light text on dark = white/yellow with black shadow
- Dark text on light = black with white stroke
- Never put text on busy backgrounds without overlay
- Test: Can you read it at a glance? If not, fix it.
"""


class MultiLineBreaking:
    """
    #120: Optimizes line breaks for readability.
    """
    
    def get_breaking_instruction(self) -> str:
        return """
LINE BREAKING RULES:
- Max 5-6 words per line
- Break at natural pauses
- Never break in middle of phrase
- Keep related words together
- "The secret to / success" NOT "The secret / to success"
- Max 2 lines on screen at once
"""


class KeyPhrasePopup:
    """
    #121: Creates pop-up effects for key phrases.
    """
    
    def get_popup_instruction(self) -> str:
        return """
KEY PHRASE POP-UPS:
- Important terms: Show in box/bubble
- Stats: Pop up with emphasis
- Quotes: Show with quotation styling
- Actions: Show as bullet points
- Creates visual variety
- Guides attention to important info
"""


class ProgressIndicator:
    """
    #122: Shows progress through video.
    """
    
    INDICATOR_TYPES = [
        "countdown_number",
        "progress_bar",
        "step_dots",
        "fraction"
    ]
    
    def get_progress_instruction(self) -> str:
        return """
PROGRESS INDICATORS:
- For list videos: "3/5" or step dots
- For countdowns: Show number
- Progress bar for tutorials
- Gives completion incentive
- "Almost there!" psychology
"""


class LowerThirdsStyle:
    """
    #123: Professional lower-thirds styling.
    """
    
    def get_lower_thirds_instruction(self) -> str:
        return """
LOWER THIRDS:
- Use for category labels, names, facts
- Keep compact and clean
- Consistent position (bottom left/right)
- Semi-transparent background
- Brand colors for recognition
- Professional look instantly
"""


class TextEntryTiming:
    """
    #124: Optimizes when text appears/disappears.
    """
    
    def get_timing_instruction(self) -> str:
        return """
TEXT TIMING:
- Text appears slightly BEFORE audio (200ms)
- Text stays slightly AFTER audio (300ms)
- Never have text change mid-word
- Sync to natural speech rhythm
- Cuts at sentence ends, not mid-thought
"""


class CalloutBoxes:
    """
    #125: Creates attention-grabbing callout boxes.
    """
    
    def get_callout_instruction(self) -> str:
        return """
CALLOUT BOXES:
- For important facts: Box with border
- For warnings: Red-bordered box
- For tips: Green checkmark box
- Keep text minimal inside
- Use 1-2 per video maximum
- Visual hierarchy = understanding
"""


class TypographyConsistency:
    """
    #126: Ensures consistent typography throughout.
    """
    
    def get_consistency_instruction(self) -> str:
        return """
TYPOGRAPHY CONSISTENCY:
- Same font family throughout
- Same color scheme (max 3 colors)
- Same animation style
- Same position zones
- Builds brand recognition
- Professional = consistent
"""


class TextBreathingRoom:
    """
    #127: Ensures text has proper spacing.
    """
    
    def get_spacing_instruction(self) -> str:
        return """
TEXT BREATHING ROOM:
- Padding around text (at least 20px)
- Line height: 1.4-1.6x font size
- Letter spacing: slightly loose for bold fonts
- Don't cram text into small spaces
- White space = readability
"""


class CaptionLengthOptimizer:
    """
    #128: Optimizes caption/subtitle length.
    """
    
    def get_length_instruction(self) -> str:
        return """
CAPTION LENGTH:
- Max 42 characters per line
- Max 2 lines at once
- Split long sentences
- Keep phrases together
- Shorter = more readable
- If it looks cramped, it IS cramped
"""


class TextHierarchy:
    """
    #129: Creates clear visual hierarchy with text.
    """
    
    def get_hierarchy_instruction(self) -> str:
        return """
TEXT HIERARCHY:
- Headlines: Largest, bold, top position
- Key points: Large, emphasized color
- Details: Medium, normal color
- Asides: Smaller, subdued color
- Clear levels = clear understanding
"""


# Master function for Typography prompts
def get_typography_master_prompt() -> str:
    """Returns comprehensive prompt for professional typography."""
    return """
# PROFESSIONAL TYPOGRAPHY GUIDELINES
Your goal: Text that looks like it was designed by a professional video editor.

## FONT SELECTION
- Bold, readable fonts (never thin/light)
- Match font to mood: Bold for power, elegant for trust
- Consistent font family throughout
- 60px minimum for mobile readability

## SIZING & EMPHASIS
- Important words: 30-40% larger
- Numbers: Slightly larger
- Power words: BIGGEST
- Whispered asides: Smaller
- Guide the eye to what matters

## COLOR & CONTRAST
- Always use text shadow/stroke
- Color-code meaning: Red=warning, Green=tip
- Max 3 colors in video
- High contrast always

## POSITIONING
- Safe zones: Not too close to edges
- Don't block faces/action
- Consistent positions
- Max 2 lines on screen

## ANIMATION
- Vary animations (fade, slide, pop)
- Match animation to content energy
- Word-by-word for key moments
- Don't overuse effects

## TIMING
- Appear slightly before audio
- Stay slightly after audio
- 3 words per second max
- Minimum 1.5 seconds on screen

## PROFESSIONALISM
- Consistent style throughout
- Clean, uncluttered
- Strategic emoji use (1-3)
- Progress indicators for lists
"""


# #############################################################################
# CATEGORY C: VOICE & AUDIO (#130-149)
# Natural, engaging voice and audio design
# #############################################################################

class VoiceTopicMatcher:
    """
    #130: Matches voice characteristics to topic.
    Authority for finance, warmth for personal advice.
    """
    
    VOICE_PROFILES = {
        "authoritative": {
            "best_for": ["finance", "business", "tech", "science"],
            "characteristics": "Deeper, measured, confident pace",
            "speed": "-10%",
            "pitch": "-5%"
        },
        "warm": {
            "best_for": ["personal", "relationships", "health", "lifestyle"],
            "characteristics": "Friendly, approachable, moderate pace",
            "speed": "0%",
            "pitch": "+5%"
        },
        "energetic": {
            "best_for": ["motivation", "fitness", "entertainment"],
            "characteristics": "Upbeat, fast, varied pitch",
            "speed": "+15%",
            "pitch": "+10%"
        },
        "mysterious": {
            "best_for": ["shocking_facts", "conspiracy", "secrets"],
            "characteristics": "Slower, dramatic pauses, lower",
            "speed": "-15%",
            "pitch": "-10%"
        },
        "conversational": {
            "best_for": ["general", "life_hacks", "fun_facts"],
            "characteristics": "Natural, like talking to friend",
            "speed": "0%",
            "pitch": "0%"
        }
    }
    
    def get_voice_for_category(self, category: str) -> Dict:
        """Get recommended voice profile for category."""
        for profile_name, profile in self.VOICE_PROFILES.items():
            if category.lower() in [c.lower() for c in profile["best_for"]]:
                return {"profile": profile_name, **profile}
        return {"profile": "conversational", **self.VOICE_PROFILES["conversational"]}


class SpeechSpeedVariation:
    """
    #131: Varies speech speed within video.
    Excitement = faster, Impact = slower.
    """
    
    SPEED_MARKERS = {
        "normal": 1.0,
        "slow_for_impact": 0.85,
        "fast_excited": 1.15,
        "dramatic_pause": 0.7,
        "quick_aside": 1.2
    }
    
    def get_speed_instruction(self) -> str:
        return """
SPEECH SPEED VARIATION:
- Hook: Normal to slightly fast (engaging)
- Key revelations: SLOW DOWN (let it sink in)
- Excitement building: Speed up gradually
- Important points: Slower, deliberate
- Transitions: Quick, keep momentum
- Never monotone speed throughout
"""


class PowerWordEmphasis:
    """
    #132: Emphasizes power words in speech.
    """
    
    POWER_WORDS = [
        "secret", "hidden", "truth", "never", "always",
        "shocking", "proven", "instant", "free", "now",
        "discover", "reveal", "exactly", "guaranteed"
    ]
    
    def get_emphasis_instruction(self) -> str:
        return """
POWER WORD EMPHASIS:
- Mark power words for vocal emphasis
- Slightly louder, slower on these words
- Brief pause BEFORE power words
- "The [pause] SECRET to success is..."
- Makes content more impactful
- AI should mark [EMPHASIZE] in script
"""


class StrategicPausing:
    """
    #133: Uses strategic pauses for effect.
    """
    
    PAUSE_TYPES = {
        "micro": 0.3,      # Between phrases
        "breath": 0.5,     # Natural breathing
        "emphasis": 0.8,   # Before important point
        "dramatic": 1.2,   # For suspense
        "absorb": 1.5      # Let info sink in
    }
    
    def get_pause_instruction(self) -> str:
        return """
STRATEGIC PAUSING:
- [MICRO_PAUSE] between phrases (0.3s)
- [BREATH] natural breathing points (0.5s)
- [EMPHASIS] before key revelations (0.8s)
- [DRAMATIC] for suspense building (1.2s)
- [ABSORB] after major points (1.5s)
- Pauses create anticipation and comprehension
"""


class PitchVariation:
    """
    #134: Varies pitch to avoid monotone.
    """
    
    def get_pitch_instruction(self) -> str:
        return """
PITCH VARIATION:
- Questions: Pitch rises at end
- Statements: Pitch falls at end
- Excitement: Higher overall pitch
- Authority: Lower, steadier pitch
- Surprise: Pitch jump
- Avoid flat, robotic monotone
"""


class VolumeDucking:
    """
    #135: Manages audio levels between voice and music.
    """
    
    def get_ducking_instruction(self) -> str:
        return """
VOLUME DUCKING:
- Music at 20-30% when speaking
- Music up between sentences
- Sound effects: Quick duck and return
- Voice should ALWAYS be clear
- Never compete with background audio
"""


class VoicePersonalityProfiles:
    """
    #136: Defines distinct voice personalities.
    """
    
    PERSONALITIES = {
        "expert": "Confident, knowledgeable, measured",
        "friend": "Casual, warm, relatable",
        "storyteller": "Engaging, varied, dramatic",
        "coach": "Motivating, energetic, encouraging",
        "investigator": "Curious, probing, mysterious"
    }
    
    def get_personality_instruction(self) -> str:
        return """
VOICE PERSONALITY:
- Pick ONE personality per video
- Expert: Confident, knowledgeable
- Friend: Casual, warm
- Storyteller: Dramatic, varied
- Coach: Motivating, energetic
- Consistency builds trust
"""


class EmotionalToneMatching:
    """
    #137: Matches voice emotion to content.
    """
    
    def get_emotion_instruction(self) -> str:
        return """
EMOTIONAL TONE MATCHING:
- Match voice emotion to content
- Serious topics: Somber, measured
- Exciting news: Energetic, upbeat
- Warnings: Concerned, serious
- Tips: Helpful, encouraging
- Emotion should match message
"""


class QuestionIntonation:
    """
    #138: Proper intonation for questions.
    """
    
    def get_question_instruction(self) -> str:
        return """
QUESTION INTONATION:
- Pitch rises at end of questions
- Rhetorical questions: Slight rise, then pause
- Open questions: Strong rise
- Tag questions: Minor rise
- "Right?" "You know?" - conversational rise
"""


class ExclamationEnergy:
    """
    #139: Delivers exclamations with appropriate energy.
    """
    
    def get_exclamation_instruction(self) -> str:
        return """
EXCLAMATION ENERGY:
- Not ALL exclamations are SHOUTED
- Genuine surprise: Higher pitch, breath
- Emphasis: Slightly louder, slower
- Warning: Lower, more serious
- Vary energy levels - don't be exhausting
"""


class WhisperEffect:
    """
    #140: Uses whisper for intimacy/secrets.
    """
    
    def get_whisper_instruction(self) -> str:
        return """
WHISPER/SOFT VOICE:
- For secrets: Slightly softer, conspiratorial
- For asides: Quieter, like sharing privately
- Use sparingly - 1-2 moments per video
- Creates intimacy and attention
- "Here's what they don't tell you..." [softer]
"""


class EchoReverb:
    """
    #141: Uses echo/reverb for emphasis.
    """
    
    def get_reverb_instruction(self) -> str:
        return """
ECHO/REVERB EFFECTS:
- Key phrases can have subtle reverb
- Creates emphasis and memorability
- Use VERY sparingly (1 per video max)
- Best for: revelations, key numbers
- Too much = cheesy
"""


class VoiceLayering:
    """
    #142: Multiple voice layers for impact.
    """
    
    def get_layering_instruction(self) -> str:
        return """
VOICE LAYERING:
- Repeat key phrase with echo
- Backup "voice" for emphasis
- Use for: numbers, key words
- "Five THOUSAND dollars" [5000 echoes]
- Creates weight and emphasis
"""


class NaturalBreathing:
    """
    #143: Includes natural breathing sounds.
    """
    
    def get_breathing_instruction(self) -> str:
        return """
NATURAL BREATHING:
- Don't edit out ALL breaths
- Subtle breathing = human
- Heavy breathing after excitement
- Breath before important points
- Completely clean audio = robotic
"""


class ConversationalFiller:
    """
    #144: Adds conversational filler sounds.
    """
    
    def get_filler_audio_instruction(self) -> str:
        return """
CONVERSATIONAL AUDIO FILLERS:
- Occasional "hmm" when thinking
- "Uh-huh" type acknowledgments
- Subtle "wow" or "huh" reactions
- Use sparingly - once per video max
- Adds humanity to delivery
"""


class ListeningCues:
    """
    #145: Verbal cues that show "listening" to viewer.
    """
    
    def get_listening_instruction(self) -> str:
        return """
LISTENING CUES (Conversational):
- "I know what you're thinking..."
- "You might be wondering..."
- "Fair question..."
- Shows you understand viewer's thoughts
- Creates two-way feel
"""


class VocalConsistency:
    """
    #146: Maintains consistent voice throughout.
    """
    
    def get_consistency_instruction(self) -> str:
        return """
VOCAL CONSISTENCY:
- Same voice profile throughout video
- Same energy level (with variations)
- Same personality
- Don't switch mid-video
- Consistency = professionalism
"""


class AccentOptimization:
    """
    #147: Optimizes accent for audience.
    """
    
    def get_accent_instruction(self) -> str:
        return """
ACCENT OPTIMIZATION:
- Clear, neutral accent for broad appeal
- Avoid strong regional accents
- Pronunciation clarity matters
- International audiences need clarity
- Understandable > Unique
"""


class AudioClarity:
    """
    #148: Ensures crystal clear audio.
    """
    
    def get_clarity_instruction(self) -> str:
        return """
AUDIO CLARITY:
- No background noise
- No echo/reverb (unless intentional)
- Clear pronunciation
- Proper microphone levels
- Quality audio = trust
- Poor audio = immediately skip
"""


class PacingRhythm:
    """
    #149: Creates rhythmic pacing in delivery.
    """
    
    def get_rhythm_instruction(self) -> str:
        return """
PACING RHYTHM:
- Build rhythm: medium, medium, PUNCH
- Vary sentence delivery speed
- Group related thoughts together
- Pause between topic shifts
- Create "beats" in your delivery
- Good pacing = easy listening
"""


# Master function for Voice & Audio prompts
def get_voice_audio_master_prompt() -> str:
    """Returns comprehensive prompt for natural voice and audio."""
    return """
# PROFESSIONAL VOICE & AUDIO GUIDELINES
Your goal: Voice that sounds like a skilled human narrator, not TTS.

## VOICE MATCHING
- Match voice to content: Authoritative for finance, warm for personal
- Pick ONE personality and maintain it
- Speed matches content: Slower for impact, faster for excitement

## VARIATION
- Speed: Vary within video (±15%)
- Pitch: Natural variation like real speech
- Volume: Slight changes for emphasis
- Never monotone

## EMPHASIS
- Power words: Slightly louder, slower, pause before
- Numbers: Extra emphasis
- Key points: Deliberate delivery
- Mark [EMPHASIZE] in script

## PAUSING
- Micro pauses between phrases (0.3s)
- Breathing pauses (0.5s)
- Emphasis pauses before revelations (0.8s)
- Absorb pauses after big points (1.5s)
- Pauses create anticipation

## EMOTION
- Match emotion to content
- Vary energy levels
- Genuine, not performative
- Enthusiasm for specifics, not everything

## NATURAL ELEMENTS
- Don't remove all breathing
- Occasional conversational sounds
- Whisper for secrets (sparingly)
- Echo for emphasis (very sparingly)

## QUALITY
- Crystal clear audio
- Voice dominates over music
- No background noise
- Professional = trustworthy
"""


# =============================================================================
# SINGLETON ACCESSORS - Categories B & C
# =============================================================================

_font_psychology = None
_dynamic_sizer = None
_word_highlight = None
_color_emphasis = None
_text_animation = None
_mobile_position = None
_reading_speed = None
_subtitle_style = None
_emoji_integration = None
_voice_matcher = None
_speed_variation = None
_power_emphasis = None
_strategic_pause = None
_pitch_variation = None


def get_font_psychology() -> FontPsychologyOptimizer:
    global _font_psychology
    if _font_psychology is None:
        _font_psychology = FontPsychologyOptimizer()
    return _font_psychology


def get_text_animation() -> TextAnimationVariety:
    global _text_animation
    if _text_animation is None:
        _text_animation = TextAnimationVariety()
    return _text_animation


def get_voice_matcher() -> VoiceTopicMatcher:
    global _voice_matcher
    if _voice_matcher is None:
        _voice_matcher = VoiceTopicMatcher()
    return _voice_matcher


# =============================================================================
# MASTER PROMPT COMBINING ALL BATCH 1 CATEGORIES
# =============================================================================

def get_batch1_human_feel_prompt() -> str:
    """Returns the complete Batch 1 prompt for human-like content."""
    anti_ai = get_anti_ai_master_prompt()
    typography = get_typography_master_prompt()
    voice = get_voice_audio_master_prompt()
    
    return f"""
################################################################################
# BATCH 1: HUMAN FEEL - ULTIMATE GUIDE
################################################################################

{anti_ai}

{typography}

{voice}

################################################################################
# SUMMARY: THE HUMAN TOUCH
################################################################################

Your content should:
1. SOUND like a real person talking (not reading)
2. LOOK professionally designed (but not sterile)
3. FEEL like a conversation (not a lecture)
4. CREATE connection (not distance)

If someone can tell it's AI-generated within 5 seconds, you've failed.
If they feel like they're learning from a knowledgeable friend, you've succeeded.

"""


# =============================================================================
# SINGLETON ACCESSORS - Category A
# =============================================================================

_natural_rhythm = None
_filler_injector = None
_breathing_pause = None
_self_correction = None
_opinion_injector = None
_colloquial = None
_rhetorical = None
_personal_perspective = None
_humor_wit = None
_imperfection = None
_emotional_inflection = None
_storytelling = None
_anecdote = None
_repetition = None
_transitions = None
_contractions = None
_direct_address = None
_confidence = None
_enthusiasm = None
_vulnerability = None


def get_natural_rhythm() -> NaturalSpeechRhythm:
    global _natural_rhythm
    if _natural_rhythm is None:
        _natural_rhythm = NaturalSpeechRhythm()
    return _natural_rhythm


def get_filler_injector() -> FillerWordInjector:
    global _filler_injector
    if _filler_injector is None:
        _filler_injector = FillerWordInjector()
    return _filler_injector


def get_breathing_pause() -> BreathingPauseSimulator:
    global _breathing_pause
    if _breathing_pause is None:
        _breathing_pause = BreathingPauseSimulator()
    return _breathing_pause


def get_self_correction() -> SelfCorrectionSimulator:
    global _self_correction
    if _self_correction is None:
        _self_correction = SelfCorrectionSimulator()
    return _self_correction


def get_opinion_injector() -> OpinionInjector:
    global _opinion_injector
    if _opinion_injector is None:
        _opinion_injector = OpinionInjector()
    return _opinion_injector


def get_colloquial() -> ColloquialLanguageDetector:
    global _colloquial
    if _colloquial is None:
        _colloquial = ColloquialLanguageDetector()
    return _colloquial


def get_rhetorical() -> RhetoricalQuestionGenerator:
    global _rhetorical
    if _rhetorical is None:
        _rhetorical = RhetoricalQuestionGenerator()
    return _rhetorical


def get_contractions_enforcer() -> ContractionsEnforcer:
    global _contractions
    if _contractions is None:
        _contractions = ContractionsEnforcer()
    return _contractions


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Enhancement Module v12.0 - Batch 1 Category A Test")
    print("=" * 60)
    
    # Test Anti-AI components
    print("\n[Category A: Anti-AI Detection]")
    
    rhythm = get_natural_rhythm()
    print(f"  NaturalSpeechRhythm: OK")
    
    filler = get_filler_injector()
    print(f"  FillerWordInjector: OK (sample: {filler.get_random_filler()})")
    
    breathing = get_breathing_pause()
    sample = "This is a test sentence that should have pauses added to it for natural speech."
    with_pauses = breathing.add_pauses_to_script(sample)
    print(f"  BreathingPauseSimulator: OK")
    
    colloquial = get_colloquial()
    formal_text = "We need to utilize this methodology to facilitate better outcomes."
    casual = colloquial.make_casual(formal_text)
    print(f"  ColloquialLanguage: OK")
    print(f"    Formal: {formal_text}")
    print(f"    Casual: {casual}")
    
    contractions = get_contractions_enforcer()
    no_contractions = "I am going to show you what you will learn. It is not hard."
    with_contractions = contractions.apply_contractions(no_contractions)
    print(f"  ContractionsEnforcer: OK")
    print(f"    Before: {no_contractions}")
    print(f"    After: {with_contractions}")
    
    print("\n" + "=" * 60)
    print("Category A: 20 Anti-AI enhancements - READY")
    print("=" * 60)


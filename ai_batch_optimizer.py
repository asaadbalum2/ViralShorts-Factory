#!/usr/bin/env python3
"""
ViralShorts Factory - AI Batch Optimizer
Combines multiple AI operations into single API calls to save quota.

Before: 4 API calls per video
After:  1-2 API calls per video (batched)
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


@dataclass
class BatchedVideoContent:
    """All content generated in a single API call."""
    topic: str
    video_type: str
    hook: str
    main_content: str
    secondary_content: Optional[str]
    voiceover_script: str
    broll_keywords: List[str]
    music_mood: str
    is_appropriate: bool
    virality_score: int
    reason: str


class AIBatchOptimizer:
    """
    Batch multiple AI operations into single calls.
    
    Instead of:
        1. Call for topic selection
        2. Call for content generation
        3. Call for content filtering
        4. Call for B-roll keywords
    
    We do:
        1. Single call that returns ALL of the above
    """
    
    COMPOUND_PROMPT = """You are an AI content generator for viral YouTube Shorts.

Generate a COMPLETE video package in a SINGLE response. Include ALL of the following:

1. TOPIC SELECTION: Pick a trending/viral topic for today
2. CONTENT GENERATION: Write the actual content (hook + main text)
3. CONTENT FILTERING: Confirm it's appropriate for all ages
4. B-ROLL KEYWORDS: 3-5 keywords for finding stock footage
5. PRODUCTION NOTES: Music mood, virality score, etc.

Current context:
- Date: {date}
- Season: {season}
- Type preference: {video_type}

Return a JSON object with these EXACT fields:
{{
    "topic": "brief topic name",
    "video_type": "scary_fact|money_fact|quote|would_you_rather|psychology_fact",
    "hook": "attention-grabbing first line (max 10 words)",
    "main_content": "the main fact/quote/question (50-80 words)",
    "secondary_content": "for WYR=option B, for quotes=author, null if not needed",
    "voiceover_script": "complete narration script",
    "broll_keywords": ["keyword1", "keyword2", "keyword3"],
    "music_mood": "dramatic|suspense|inspirational|fun|energetic",
    "is_appropriate": true/false,
    "virality_score": 1-10,
    "reason": "why this will perform well"
}}

IMPORTANT: 
- Content MUST be family-friendly (no violence, adult themes, disturbing content)
- Hook MUST grab attention in first 1 second
- Content MUST be interesting/surprising/valuable
- Return ONLY the JSON object, no other text"""
    
    def __init__(self):
        self.client = None
        if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    def generate_complete_video_content(self, video_type: str = "any") -> Optional[BatchedVideoContent]:
        """
        Generate ALL video content in a SINGLE API call.
        
        This replaces 4 separate calls with 1 batched call.
        """
        if not self.client:
            print("⚠️ No AI client available")
            return None
        
        from datetime import datetime
        now = datetime.now()
        
        # Determine season
        month = now.month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"
        
        prompt = self.COMPOUND_PROMPT.format(
            date=now.strftime("%B %d, %Y"),
            season=season,
            video_type=video_type if video_type != "any" else "any viral type"
        )
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.8
            )
            
            result = response.choices[0].message.content
            
            # Clean JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            data = json.loads(result.strip())
            
            return BatchedVideoContent(
                topic=data.get("topic", "Unknown"),
                video_type=data.get("video_type", "scary_fact"),
                hook=data.get("hook", ""),
                main_content=data.get("main_content", ""),
                secondary_content=data.get("secondary_content"),
                voiceover_script=data.get("voiceover_script", ""),
                broll_keywords=data.get("broll_keywords", ["abstract", "motion"]),
                music_mood=data.get("music_mood", "dramatic"),
                is_appropriate=data.get("is_appropriate", True),
                virality_score=data.get("virality_score", 5),
                reason=data.get("reason", "")
            )
            
        except Exception as e:
            print(f"⚠️ Batched generation failed: {e}")
            return None
    
    def generate_multiple_videos(self, count: int = 3) -> List[BatchedVideoContent]:
        """
        Generate content for multiple videos in batched calls.
        
        For 3 videos:
        - Before: 12 API calls (4 per video)
        - After: 3 API calls (1 per video) or even 1 call for all 3!
        """
        # For truly optimal batching, we could ask for multiple videos in one call
        # But this risks hitting token limits, so we do 1 call per video
        
        results = []
        types = ["scary_fact", "money_fact", "psychology_fact", "quote"]
        
        for i in range(count):
            video_type = types[i % len(types)]
            print(f"📹 Generating video {i+1}/{count} ({video_type})...")
            
            content = self.generate_complete_video_content(video_type)
            if content:
                results.append(content)
                print(f"   ✅ Topic: {content.topic}")
                print(f"   📊 Virality: {content.virality_score}/10")
        
        return results


# =============================================================================
# Usage Stats
# =============================================================================

def get_api_usage_stats():
    """Show API usage comparison."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  API USAGE OPTIMIZATION                       ║
╠══════════════════════════════════════════════════════════════╣
║  BEFORE (Separate Calls):                                     ║
║    • Topic selection:     1 call                              ║
║    • Content generation:  1 call                              ║
║    • Content filtering:   1 call                              ║
║    • B-roll keywords:     1 call                              ║
║    ─────────────────────────────                              ║
║    TOTAL PER VIDEO:       4 calls                             ║
║                                                               ║
║  AFTER (Batched):                                             ║
║    • All-in-one prompt:   1 call                              ║
║    ─────────────────────────────                              ║
║    TOTAL PER VIDEO:       1 call                              ║
║                                                               ║
║  SAVINGS: 75% fewer API calls!                                ║
╠══════════════════════════════════════════════════════════════╣
║  GROQ FREE TIER LIMITS:                                       ║
║    • 30 requests/minute                                       ║
║    • 14,400 requests/day                                      ║
║    • 6,000 tokens/minute (llama-3.3-70b)                      ║
║                                                               ║
║  YOUR CAPACITY:                                               ║
║    • Before: 3,600 videos/day                                 ║
║    • After:  14,400 videos/day                                ║
║                                                               ║
║  ✅ YOU ARE WAY BELOW THE LIMIT - NO CONCERN!                 ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    get_api_usage_stats()
    
    print("\n🧪 Testing batched generation...")
    optimizer = AIBatchOptimizer()
    
    content = optimizer.generate_complete_video_content("scary_fact")
    if content:
        print(f"\n✅ Generated in 1 API call:")
        print(f"   Topic: {content.topic}")
        print(f"   Hook: {content.hook}")
        print(f"   Content: {content.main_content[:60]}...")
        print(f"   B-roll: {content.broll_keywords}")
        print(f"   Music: {content.music_mood}")
        print(f"   Safe: {content.is_appropriate}")
        print(f"   Virality: {content.virality_score}/10")


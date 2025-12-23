#!/usr/bin/env python3
"""
Monthly Viral Analysis Script
Analyzes top-performing AI-generated YouTube Shorts and extracts patterns
for the ViralShorts Factory to use.
"""

import os
import json
import requests
import re
from datetime import datetime
from pathlib import Path

# API Keys - Use OAuth credentials (same as upload)
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

ANALYSIS_FILE = Path("data/persistent/monthly_analysis.json")
VIRAL_PATTERNS_FILE = Path("data/persistent/viral_patterns.json")

# YouTube access token (refreshed at runtime)
_youtube_access_token = None


def safe_print(msg):
    """Print message safely, handling Unicode."""
    try:
        print(msg)
    except:
        print(msg.encode('ascii', 'ignore').decode())


def get_youtube_access_token():
    """Get YouTube access token using OAuth refresh token."""
    global _youtube_access_token
    if _youtube_access_token:
        return _youtube_access_token
    
    if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN]):
        safe_print("[!] Missing YouTube OAuth credentials")
        return None
    
    try:
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": YOUTUBE_CLIENT_ID,
                "client_secret": YOUTUBE_CLIENT_SECRET,
                "refresh_token": YOUTUBE_REFRESH_TOKEN,
                "grant_type": "refresh_token"
            },
            timeout=10
        )
        if response.status_code == 200:
            _youtube_access_token = response.json().get("access_token")
            safe_print("[OK] YouTube OAuth token refreshed")
            return _youtube_access_token
        else:
            safe_print(f"[!] Token refresh failed: {response.status_code}")
    except Exception as e:
        safe_print(f"[!] Token refresh error: {e}")
    return None


def youtube_search(query, max_results=10):
    """Search YouTube for videos using OAuth."""
    token = get_youtube_access_token()
    if not token:
        safe_print("[!] No YouTube access token")
        return []
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "videoDuration": "short",  # Shorts only
        "order": "viewCount",
        "maxResults": max_results,
        "publishedAfter": "2024-01-01T00:00:00Z"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get("items", [])
        else:
            safe_print(f"[!] Search failed: {response.status_code}")
    except Exception as e:
        safe_print(f"[!] Search error: {e}")
    return []


def get_video_details(video_ids):
    """Get detailed stats for videos using OAuth."""
    token = get_youtube_access_token()
    if not token or not video_ids:
        return []
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "id": ",".join(video_ids),
        "part": "statistics,snippet,contentDetails"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get("items", [])
        else:
            safe_print(f"[!] Details failed: {response.status_code}")
    except Exception as e:
        safe_print(f"[!] Details error: {e}")
    return []


def analyze_with_ai(videos_data):
    """Use AI for MICRO-LEVEL analysis of successful videos.
    Extracts GOLD-VALUE: tricks, baits, hacks, psychological triggers.
    """
    if not GROQ_API_KEY or not videos_data:
        return {}
    
    prompt = f"""You are a viral video reverse-engineer. Extract EVERY secret from these successful YouTube Shorts:

VIDEO DATA (from viral competitors):
{json.dumps(videos_data, indent=2)}

Extract GOLD-VALUE patterns - the TRICKS, BAITS, and HACKS that made these go viral:

1. **TITLE TRICKS**: Numbers? Power words? Curiosity gaps? Click-bait techniques?
2. **HOOK HACKS**: What grabs attention in first 1-2 seconds? Shocking statements? Questions?
3. **PSYCHOLOGICAL TRIGGERS**: FOMO? Curiosity? Controversy? Social proof? Fear? Greed?
4. **ENGAGEMENT BAITS**: How do they farm comments? "Comment 1 if...", "Tag someone who..."
5. **CONTENT SECRETS**: What makes the content irresistible? Secrets? Hacks? Hidden truths?
6. **RETENTION TRICKS**: How do they keep viewers watching? Open loops? Countdowns?
7. **VIRALITY HACKS**: Shareability factors? Controversy? Relatability?
8. **MUSIC/MOOD**: Dramatic? Mysterious? Upbeat? What amplifies emotion?
9. **TOPIC ANGLES**: What specific angles within categories work best?
10. **CTA TRICKS**: How do they convert viewers to subscribers/commenters?

Return comprehensive GOLD-VALUE JSON:
{{
    "title_tricks": ["use X number", "curiosity gap with...", ...],
    "title_patterns": ["pattern with {{placeholder}}", ...],
    "hook_hacks": ["start with question", "shocking first word", ...],
    "psychological_triggers": ["fomo", "curiosity", "controversy", ...],
    "engagement_baits": ["comment 1 if you...", "tag someone who...", ...],
    "retention_tricks": ["open loop", "countdown", ...],
    "virality_hacks": ["make it shareable by...", ...],
    "top_categories": ["category1", "category2", ...],
    "hook_patterns": ["specific hook technique", ...],
    "music_moods_that_work": ["dramatic", "mysterious", ...],
    "visual_keywords": ["keyword for b-roll", ...],
    "voice_styles": ["energetic", "calm", ...],
    "optimal_phrase_count": number,
    "optimal_duration_seconds": number,
    "content_themes": ["secrets about X", "hacks for Y", ...],
    "insights": ["key gold-value insight 1", "insight 2", ...]
}}

Be SPECIFIC. Extract the SECRETS that make these videos viral. JSON ONLY."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Best model for analysis
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                return json.loads(match.group())
    except Exception as e:
        safe_print(f"[!] AI analysis error: {e}")
    return {}


def generate_search_queries_ai():
    """AI generates search queries - NO HARDCODING!"""
    if not GROQ_API_KEY:
        return ["viral shorts 2024", "facts shorts trending"]
    
    prompt = """You are a YouTube search expert. Generate 5-7 search queries to find the most viral AI-generated YouTube Shorts in 2024-2025.

We want to find:
- Fact-based Shorts with millions of views
- AI voiceover content that went viral
- Psychology, money, life hack content
- Any AI-generated short-form content that succeeded

Return a JSON array of search queries:
["query 1", "query 2", ...]

Be specific and use terms that will find HIGH-VIEW viral content.
JSON ARRAY ONLY."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 200
            },
            timeout=10
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                queries = json.loads(match.group())
                if queries and len(queries) >= 3:
                    safe_print(f"[AI] Generated {len(queries)} search queries")
                    return queries
    except Exception as e:
        safe_print(f"[!] AI query generation failed: {e}")
    
    # Minimal fallback only if AI completely fails
    return ["viral shorts 2024 million views", "trending facts shorts"]


def main():
    """Main analysis flow."""
    safe_print("=" * 60)
    safe_print("MONTHLY VIRAL ANALYSIS")
    safe_print(f"Date: {datetime.now().isoformat()}")
    safe_print("=" * 60)

    # Ensure directories exist
    Path("data/persistent").mkdir(parents=True, exist_ok=True)
    Path("data/analysis").mkdir(parents=True, exist_ok=True)

    # AI-generated search queries - NOT HARDCODED!
    safe_print("\n[AI] Generating search queries...")
    search_queries = generate_search_queries_ai()
    safe_print(f"[OK] Will search: {search_queries}")

    all_videos = []
    seen_ids = set()

    for query in search_queries:
        safe_print(f"\n[SEARCH] {query}")
        results = youtube_search(query, max_results=5)
        
        for item in results:
            vid_id = item.get("id", {}).get("videoId")
            if vid_id and vid_id not in seen_ids:
                seen_ids.add(vid_id)
                all_videos.append({
                    "id": vid_id,
                    "title": item.get("snippet", {}).get("title", ""),
                    "channel": item.get("snippet", {}).get("channelTitle", ""),
                    "published": item.get("snippet", {}).get("publishedAt", "")
                })

    safe_print(f"\n[FOUND] {len(all_videos)} unique videos")

    # Get detailed stats
    if all_videos:
        video_ids = [v["id"] for v in all_videos[:20]]  # Limit API calls
        details = get_video_details(video_ids)
        
        # Merge stats
        stats_map = {d["id"]: d for d in details}
        for video in all_videos:
            if video["id"] in stats_map:
                stats = stats_map[video["id"]]
                video["views"] = int(stats.get("statistics", {}).get("viewCount", 0))
                video["likes"] = int(stats.get("statistics", {}).get("likeCount", 0))
                video["comments"] = int(stats.get("statistics", {}).get("commentCount", 0))

    # Sort by views
    all_videos.sort(key=lambda x: x.get("views", 0), reverse=True)
    top_videos = all_videos[:10]

    safe_print("\n[TOP VIDEOS]")
    for i, v in enumerate(top_videos, 1):
        safe_print(f"  {i}. {v.get('views', 0):,} views - {v.get('title', 'N/A')[:50]}")

    # AI Analysis
    safe_print("\n[AI ANALYSIS]")
    analysis = analyze_with_ai(top_videos)

    if analysis:
        safe_print(f"  Title patterns: {len(analysis.get('title_patterns', []))}")
        safe_print(f"  Top categories: {analysis.get('top_categories', [])}")
        safe_print(f"  Key insights: {len(analysis.get('insights', []))}")
        
        # Save analysis results
        analysis_result = {
            "date": datetime.now().isoformat(),
            "videos_analyzed": len(top_videos),
            "top_video_views": top_videos[0].get("views", 0) if top_videos else 0,
            "patterns": analysis,
            "raw_videos": top_videos
        }
        
        with open(ANALYSIS_FILE, 'w') as f:
            json.dump(analysis_result, f, indent=2)
        
        # Update viral patterns file for use by video generator
        existing_patterns = {}
        if VIRAL_PATTERNS_FILE.exists():
            try:
                with open(VIRAL_PATTERNS_FILE, 'r') as f:
                    existing_patterns = json.load(f)
            except:
                pass
        
        # Merge ALL micro-level patterns including GOLD-VALUE fields
        array_keys = [
            "title_patterns", "hook_patterns", "engagement_baits",
            "music_moods_that_work", "visual_keywords", "voice_styles",
            "content_themes",
            # GOLD-VALUE fields
            "title_tricks", "hook_hacks", "psychological_triggers",
            "retention_tricks", "virality_hacks"
        ]
        for key in array_keys:
            if key in analysis:
                existing = existing_patterns.get(key, [])
                for item in analysis[key]:
                    if item not in existing:
                        existing.append(item)
                existing_patterns[key] = existing[-20:]  # Keep last 20
        
        # Direct value updates
        if analysis.get("top_categories"):
            existing_patterns["proven_categories"] = analysis["top_categories"]
        
        if analysis.get("insights"):
            existing_patterns["latest_insights"] = analysis["insights"]
        
        if analysis.get("optimal_duration_seconds"):
            existing_patterns["optimal_duration"] = analysis["optimal_duration_seconds"]
        
        if analysis.get("optimal_phrase_count"):
            existing_patterns["optimal_phrase_count"] = analysis["optimal_phrase_count"]
        
        existing_patterns["last_updated"] = datetime.now().isoformat()
        existing_patterns["ai_generated"] = True
        existing_patterns["source"] = "youtube_analysis"
        
        with open(VIRAL_PATTERNS_FILE, 'w') as f:
            json.dump(existing_patterns, f, indent=2)
        
        safe_print("\n[SAVED] Patterns updated for video generation")
    else:
        safe_print("[!] AI analysis returned no results")

    safe_print("\n" + "=" * 60)
    safe_print("ANALYSIS COMPLETE")
    safe_print("=" * 60)


if __name__ == "__main__":
    main()


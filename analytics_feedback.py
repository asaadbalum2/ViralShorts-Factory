#!/usr/bin/env python3
"""
ViralShorts Factory - Analytics Feedback Loop System
======================================================

This system:
1. Tracks metadata for every video we generate
2. Fetches performance metrics (views, likes, comments)
3. Uses AI to analyze what works and what doesn't
4. Feeds insights back into content generation

THE GOAL: Learn and improve automatically!

Data Flow:
[Generate Video] → [Save Metadata] → [Upload] → [Wait] → 
[Fetch Analytics] → [AI Analysis] → [Update Preferences] → [Better Videos!]
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import requests


# =============================================================================
# VIDEO METADATA TRACKING
# =============================================================================

@dataclass
class VideoMetadata:
    """Complete metadata for a generated video."""
    # Identification
    video_id: str
    local_path: str
    filename: str
    
    # Content
    topic: str
    video_type: str
    hook: str
    content_summary: str
    
    # Generation details
    broll_keywords: List[str]
    music_mood: str
    voiceover_style: str
    theme_name: str
    
    # AI scores (pre-upload)
    value_check_score: int
    virality_score: int
    timeliness_score: int
    
    # Platform details
    platforms_uploaded: List[str]
    youtube_video_id: Optional[str]
    dailymotion_video_id: Optional[str]
    
    # Timestamps
    generated_at: str
    uploaded_at: Optional[str]
    
    # Performance (updated later)
    performance: Optional[Dict] = None


class VideoMetadataStore:
    """
    Store and retrieve video metadata.
    
    Saves to JSON file for persistence across runs.
    """
    
    def __init__(self, store_path: str = "data/video_metadata.json"):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata: Dict[str, VideoMetadata] = {}
        self._load()
    
    def _load(self):
        """Load metadata from file."""
        if self.store_path.exists():
            try:
                with open(self.store_path, 'r') as f:
                    data = json.load(f)
                    for vid_id, meta in data.items():
                        self.metadata[vid_id] = VideoMetadata(**meta)
            except Exception as e:
                print(f"⚠️ Error loading metadata: {e}")
    
    def _save(self):
        """Save metadata to file."""
        try:
            data = {vid_id: asdict(meta) for vid_id, meta in self.metadata.items()}
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Error saving metadata: {e}")
    
    def add(self, metadata: VideoMetadata):
        """Add new video metadata."""
        self.metadata[metadata.video_id] = metadata
        self._save()
        print(f"📝 Saved metadata for: {metadata.video_id}")
    
    def update_performance(self, video_id: str, performance: Dict):
        """Update performance metrics for a video."""
        if video_id in self.metadata:
            self.metadata[video_id].performance = performance
            self._save()
            print(f"📊 Updated performance for: {video_id}")
    
    def get_all(self) -> List[VideoMetadata]:
        """Get all video metadata."""
        return list(self.metadata.values())
    
    def get_recent(self, days: int = 7) -> List[VideoMetadata]:
        """Get videos from the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        for meta in self.metadata.values():
            try:
                gen_time = datetime.fromisoformat(meta.generated_at)
                if gen_time > cutoff:
                    recent.append(meta)
            except:
                pass
        return recent
    
    def get_top_performers(self, limit: int = 10) -> List[VideoMetadata]:
        """Get top performing videos by views."""
        with_performance = [m for m in self.metadata.values() if m.performance]
        sorted_videos = sorted(
            with_performance,
            key=lambda x: x.performance.get("views", 0),
            reverse=True
        )
        return sorted_videos[:limit]


# =============================================================================
# YOUTUBE ANALYTICS FETCHER
# =============================================================================

class YouTubeAnalyticsFetcher:
    """
    Fetch video analytics from YouTube.
    
    Uses the YouTube Data API to get:
    - View count
    - Like count
    - Comment count
    - Watch time (if available)
    """
    
    def __init__(self):
        self.client_id = os.environ.get("YOUTUBE_CLIENT_ID")
        self.client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
        self.access_token = None
    
    def _get_access_token(self) -> Optional[str]:
        """Get fresh access token."""
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return None
        
        try:
            response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                return self.access_token
        except Exception as e:
            print(f"⚠️ Error getting access token: {e}")
        return None
    
    def get_video_stats(self, video_id: str) -> Optional[Dict]:
        """
        Get statistics for a specific video.
        
        Returns: {views, likes, comments, published_at}
        """
        if not self.access_token:
            if not self._get_access_token():
                return None
        
        try:
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "statistics,snippet",
                    "id": video_id,
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    item = data["items"][0]
                    stats = item.get("statistics", {})
                    snippet = item.get("snippet", {})
                    
                    return {
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "title": snippet.get("title", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "fetched_at": datetime.now().isoformat(),
                    }
        except Exception as e:
            print(f"⚠️ Error fetching video stats: {e}")
        
        return None
    
    def get_channel_videos(self, max_results: int = 50) -> List[Dict]:
        """Get recent videos from our channel."""
        if not self.access_token:
            if not self._get_access_token():
                return []
        
        try:
            # First get channel uploads playlist
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "part": "contentDetails",
                    "mine": "true",
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code != 200:
                return []
            
            channel_data = response.json()
            if not channel_data.get("items"):
                return []
            
            uploads_playlist = channel_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Get videos from uploads playlist
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "part": "snippet",
                    "playlistId": uploads_playlist,
                    "maxResults": max_results,
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                videos = []
                for item in response.json().get("items", []):
                    videos.append({
                        "video_id": item["snippet"]["resourceId"]["videoId"],
                        "title": item["snippet"]["title"],
                        "published_at": item["snippet"]["publishedAt"],
                    })
                return videos
        except Exception as e:
            print(f"⚠️ Error fetching channel videos: {e}")
        
        return []


# =============================================================================
# AI-POWERED ANALYTICS ANALYZER
# =============================================================================

class AnalyticsAnalyzer:
    """
    Use AI to analyze performance data and extract insights.
    
    This is the BRAIN that learns from our video performance!
    """
    
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.client = None
        
        if self.groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.groq_key)
            except ImportError:
                pass
    
    def analyze_performance(self, videos: List[VideoMetadata]) -> Dict:
        """
        Analyze video performance and extract actionable insights.
        
        Returns insights about:
        - Which topics perform best
        - Which video types get most engagement
        - What hooks work
        - What music moods are effective
        - What to do MORE of and LESS of
        """
        if not self.client:
            return self._basic_analysis(videos)
        
        # Prepare data for AI analysis
        video_data = []
        for v in videos:
            if v.performance:
                video_data.append({
                    "topic": v.topic,
                    "video_type": v.video_type,
                    "hook": v.hook[:50],
                    "music_mood": v.music_mood,
                    "views": v.performance.get("views", 0),
                    "likes": v.performance.get("likes", 0),
                    "comments": v.performance.get("comments", 0),
                    "virality_score": v.virality_score,
                })
        
        if not video_data:
            return {"error": "No performance data available"}
        
        prompt = f"""You are a YouTube Shorts analytics expert. Analyze this video performance data and provide actionable insights.

VIDEO DATA:
{json.dumps(video_data, indent=2)}

Analyze the data and provide:

1. TOP PERFORMERS: Which videos performed best and why?

2. TOPIC ANALYSIS: Which topics get the most views/engagement?

3. VIDEO TYPE ANALYSIS: Which video types (psychology_fact, life_hack, etc.) perform best?

4. HOOK ANALYSIS: What hook patterns lead to better performance?

5. MUSIC MOOD ANALYSIS: Does music mood affect performance?

6. RECOMMENDATIONS:
   - What should we do MORE of?
   - What should we AVOID?
   - Specific topic suggestions for next videos

Return as JSON:
{{
    "top_performers": ["topic1", "topic2"],
    "best_video_types": ["type1", "type2"],
    "best_hooks_patterns": ["pattern1", "pattern2"],
    "best_music_moods": ["mood1", "mood2"],
    "do_more": ["recommendation1", "recommendation2"],
    "do_less": ["thing_to_avoid1", "thing_to_avoid2"],
    "next_video_suggestions": ["suggestion1", "suggestion2", "suggestion3"],
    "key_insight": "One sentence summary of most important finding"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            return json.loads(result.strip())
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            return self._basic_analysis(videos)
    
    def _basic_analysis(self, videos: List[VideoMetadata]) -> Dict:
        """Basic analysis without AI."""
        with_performance = [v for v in videos if v.performance]
        
        if not with_performance:
            return {"error": "No performance data"}
        
        # Simple analysis
        total_views = sum(v.performance.get("views", 0) for v in with_performance)
        avg_views = total_views / len(with_performance)
        
        # Find best video type
        type_views = {}
        for v in with_performance:
            vtype = v.video_type
            if vtype not in type_views:
                type_views[vtype] = []
            type_views[vtype].append(v.performance.get("views", 0))
        
        best_type = max(type_views.keys(), key=lambda t: sum(type_views[t]) / len(type_views[t]))
        
        return {
            "total_videos": len(with_performance),
            "total_views": total_views,
            "average_views": avg_views,
            "best_video_type": best_type,
            "key_insight": f"Average of {avg_views:.0f} views. {best_type} performs best.",
        }
    
    def get_content_recommendations(self, insights: Dict) -> Dict:
        """
        Convert insights into actionable content recommendations.
        
        This feeds back into the content generation system!
        """
        recommendations = {
            "preferred_video_types": insights.get("best_video_types", []),
            "preferred_topics": insights.get("top_performers", []),
            "preferred_music_moods": insights.get("best_music_moods", []),
            "avoid_topics": insights.get("do_less", []),
            "next_videos": insights.get("next_video_suggestions", []),
        }
        
        return recommendations


# =============================================================================
# FEEDBACK LOOP CONTROLLER
# =============================================================================

class FeedbackLoopController:
    """
    Main controller that orchestrates the feedback loop.
    
    1. Saves metadata when videos are generated
    2. Periodically fetches performance data
    3. Analyzes performance with AI
    4. Updates content preferences
    """
    
    def __init__(self):
        self.metadata_store = VideoMetadataStore()
        self.youtube_fetcher = YouTubeAnalyticsFetcher()
        self.analyzer = AnalyticsAnalyzer()
        
        # Content preferences (updated by analytics)
        self.preferences_path = Path("data/content_preferences.json")
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict:
        """Load content preferences."""
        if self.preferences_path.exists():
            try:
                with open(self.preferences_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default preferences
        return {
            "preferred_video_types": [],
            "preferred_topics": [],
            "preferred_music_moods": [],
            "avoid_topics": [],
            "last_updated": None,
        }
    
    def _save_preferences(self):
        """Save content preferences."""
        self.preferences_path.parent.mkdir(parents=True, exist_ok=True)
        self.preferences["last_updated"] = datetime.now().isoformat()
        with open(self.preferences_path, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def record_video_generation(self, 
                                  video_id: str,
                                  local_path: str,
                                  topic_data: Dict) -> VideoMetadata:
        """
        Record metadata when a video is generated.
        
        Call this right after video generation!
        """
        metadata = VideoMetadata(
            video_id=video_id,
            local_path=local_path,
            filename=Path(local_path).name,
            topic=topic_data.get("topic", "Unknown"),
            video_type=topic_data.get("video_type", "unknown"),
            hook=topic_data.get("hook", ""),
            content_summary=topic_data.get("content", "")[:200],
            broll_keywords=topic_data.get("broll_keywords", []),
            music_mood=topic_data.get("music_mood", "dramatic"),
            voiceover_style="energetic",  # Could be customized
            theme_name="dynamic",
            value_check_score=topic_data.get("value_check", {}).get("score", 0),
            virality_score=topic_data.get("virality_score", 0),
            timeliness_score=topic_data.get("timeliness_score", 0),
            platforms_uploaded=[],
            youtube_video_id=None,
            dailymotion_video_id=None,
            generated_at=datetime.now().isoformat(),
            uploaded_at=None,
            performance=None,
        )
        
        self.metadata_store.add(metadata)
        return metadata
    
    def record_upload(self, video_id: str, platform: str, platform_video_id: str):
        """Record when a video is uploaded to a platform."""
        if video_id in self.metadata_store.metadata:
            meta = self.metadata_store.metadata[video_id]
            meta.platforms_uploaded.append(platform)
            meta.uploaded_at = datetime.now().isoformat()
            
            if platform == "youtube":
                meta.youtube_video_id = platform_video_id
            elif platform == "dailymotion":
                meta.dailymotion_video_id = platform_video_id
            
            self.metadata_store._save()
    
    def update_all_performance(self) -> int:
        """
        Fetch and update performance for all videos with YouTube IDs.
        
        Returns number of videos updated.
        """
        updated = 0
        
        for video_id, meta in self.metadata_store.metadata.items():
            if meta.youtube_video_id:
                stats = self.youtube_fetcher.get_video_stats(meta.youtube_video_id)
                if stats:
                    self.metadata_store.update_performance(video_id, stats)
                    updated += 1
        
        print(f"📊 Updated performance for {updated} videos")
        return updated
    
    def run_analysis(self) -> Dict:
        """
        Run full analytics analysis and update preferences.
        """
        # Get videos with performance data
        all_videos = self.metadata_store.get_all()
        
        # Analyze
        insights = self.analyzer.analyze_performance(all_videos)
        
        # Update preferences
        recommendations = self.analyzer.get_content_recommendations(insights)
        
        self.preferences.update(recommendations)
        self._save_preferences()
        
        print("\n📈 Analytics Analysis Complete!")
        print(f"   Key Insight: {insights.get('key_insight', 'N/A')}")
        
        return insights
    
    def get_content_guidance(self) -> Dict:
        """
        Get guidance for next content generation based on analytics.
        
        Use this when generating new videos!
        """
        return {
            "preferred_types": self.preferences.get("preferred_video_types", []),
            "suggested_topics": self.preferences.get("next_videos", []),
            "avoid": self.preferences.get("avoid_topics", []),
            "preferred_moods": self.preferences.get("preferred_music_moods", []),
        }


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'VideoMetadata',
    'VideoMetadataStore',
    'YouTubeAnalyticsFetcher',
    'AnalyticsAnalyzer',
    'FeedbackLoopController',
]


if __name__ == "__main__":
    print("=" * 60)
    print("📊 Analytics Feedback Loop System")
    print("=" * 60)
    
    controller = FeedbackLoopController()
    
    print("\n📋 Current Preferences:")
    for key, value in controller.preferences.items():
        print(f"   {key}: {value}")
    
    print("\n📈 Fetching YouTube Analytics...")
    fetcher = YouTubeAnalyticsFetcher()
    
    # Try to get channel videos
    videos = fetcher.get_channel_videos(10)
    print(f"   Found {len(videos)} videos")
    
    for video in videos[:3]:
        print(f"   - {video['title'][:50]}...")
        stats = fetcher.get_video_stats(video['video_id'])
        if stats:
            print(f"     Views: {stats['views']}, Likes: {stats['likes']}")
    
    print("\n🎯 Content Guidance for Next Video:")
    guidance = controller.get_content_guidance()
    for key, value in guidance.items():
        print(f"   {key}: {value}")


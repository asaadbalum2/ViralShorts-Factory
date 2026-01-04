#!/usr/bin/env python3
"""
v17.9.10: AI Video Generation Integration
==========================================

Optional integration with AI video generation APIs for unique B-roll content.
These complement (not replace) Pexels stock footage.

Supported APIs:
- Veo 3.1 (veo3api.com) - ~100 monthly credits, text-to-video
- Runware.ai - Free test credits, image/video generation
- Runway Gen-4 (via free wrappers) - Text-to-video

Usage:
    generator = AIVideoGenerator()
    video_path = generator.generate_clip("A futuristic city at night", duration=5)
"""

import os
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Cache directory for generated clips
CACHE_DIR = Path("cache/ai_videos")
USAGE_FILE = CACHE_DIR / "usage_tracking.json"


class AIVideoGenerator:
    """Generate short video clips using AI APIs."""
    
    def __init__(self):
        """Initialize with available API keys."""
        self.veo_api_key = os.environ.get("VEO_API_KEY")
        self.runware_api_key = os.environ.get("RUNWARE_API_KEY")
        
        # Track which APIs are available
        self.available_apis = []
        if self.veo_api_key:
            self.available_apis.append("veo")
        if self.runware_api_key:
            self.available_apis.append("runware")
        
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_usage()
    
    def _load_usage(self):
        """Load usage tracking data."""
        try:
            if USAGE_FILE.exists():
                with open(USAGE_FILE, 'r') as f:
                    self.usage = json.load(f)
            else:
                self.usage = {
                    "veo": {"used": 0, "limit": 100, "last_reset": None},
                    "runware": {"used": 0, "limit": 50, "last_reset": None}
                }
        except:
            self.usage = {"veo": {"used": 0, "limit": 100}, "runware": {"used": 0, "limit": 50}}
    
    def _save_usage(self):
        """Save usage tracking data."""
        try:
            with open(USAGE_FILE, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except:
            pass
    
    def is_available(self) -> bool:
        """Check if any AI video API is available and has quota."""
        for api in self.available_apis:
            if self.usage.get(api, {}).get("used", 0) < self.usage.get(api, {}).get("limit", 0):
                return True
        return False
    
    def get_remaining_credits(self) -> Dict[str, int]:
        """Get remaining credits for each API."""
        result = {}
        for api in ["veo", "runware"]:
            used = self.usage.get(api, {}).get("used", 0)
            limit = self.usage.get(api, {}).get("limit", 0)
            result[api] = max(0, limit - used)
        return result
    
    def generate_clip(self, prompt: str, duration: int = 5, 
                     output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a short video clip from a text prompt.
        
        Args:
            prompt: Text description of the video to generate
            duration: Target duration in seconds (3-10 typically)
            output_path: Optional path to save the video
        
        Returns:
            Path to generated video file, or None if failed
        """
        # Try APIs in order of remaining quota
        apis_by_quota = sorted(
            self.available_apis,
            key=lambda x: self.usage.get(x, {}).get("limit", 0) - self.usage.get(x, {}).get("used", 0),
            reverse=True
        )
        
        for api in apis_by_quota:
            remaining = self.usage.get(api, {}).get("limit", 0) - self.usage.get(api, {}).get("used", 0)
            if remaining <= 0:
                continue
            
            if api == "veo":
                result = self._generate_veo(prompt, duration, output_path)
            elif api == "runware":
                result = self._generate_runware(prompt, duration, output_path)
            else:
                continue
            
            if result:
                self.usage[api]["used"] = self.usage[api].get("used", 0) + 1
                self._save_usage()
                return result
        
        return None
    
    def _generate_veo(self, prompt: str, duration: int, output_path: Optional[str]) -> Optional[str]:
        """Generate video using Veo 3.1 API."""
        if not self.veo_api_key:
            return None
        
        try:
            # Veo 3.1 API endpoint (veo3api.com)
            response = requests.post(
                "https://api.veo3api.com/v1/generate",
                headers={
                    "Authorization": f"Bearer {self.veo_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "duration": duration,
                    "style": "cinematic",  # Options: cinematic, realistic, animated
                    "resolution": "1080p"
                },
                timeout=120  # Video generation can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("video_url")
                
                if video_url:
                    # Download video
                    video_response = requests.get(video_url, timeout=60)
                    if video_response.status_code == 200:
                        path = output_path or str(CACHE_DIR / f"veo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                        with open(path, 'wb') as f:
                            f.write(video_response.content)
                        return path
        except Exception as e:
            print(f"[Veo] Generation failed: {e}")
        
        return None
    
    def _generate_runware(self, prompt: str, duration: int, output_path: Optional[str]) -> Optional[str]:
        """Generate video using Runware API."""
        if not self.runware_api_key:
            return None
        
        try:
            # Runware API endpoint
            response = requests.post(
                "https://api.runware.ai/v1/video/generate",
                headers={
                    "Authorization": f"Bearer {self.runware_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "num_seconds": duration,
                    "model": "text-to-video"
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("output", [{}])[0].get("url")
                
                if video_url:
                    video_response = requests.get(video_url, timeout=60)
                    if video_response.status_code == 200:
                        path = output_path or str(CACHE_DIR / f"runware_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                        with open(path, 'wb') as f:
                            f.write(video_response.content)
                        return path
        except Exception as e:
            print(f"[Runware] Generation failed: {e}")
        
        return None


def get_ai_video_generator() -> AIVideoGenerator:
    """Get singleton instance of AI video generator."""
    if not hasattr(get_ai_video_generator, "_instance"):
        get_ai_video_generator._instance = AIVideoGenerator()
    return get_ai_video_generator._instance


def is_ai_video_available() -> bool:
    """Check if AI video generation is available."""
    generator = get_ai_video_generator()
    return generator.is_available()


def generate_ai_broll(keyword: str, duration: int = 5) -> Optional[str]:
    """
    Generate AI B-roll for a keyword.
    
    This can be used as an alternative/supplement to Pexels stock footage.
    
    Args:
        keyword: Subject of the B-roll (e.g., "money growing", "brain neurons")
        duration: Length in seconds
    
    Returns:
        Path to generated video, or None if unavailable
    """
    generator = get_ai_video_generator()
    if not generator.is_available():
        return None
    
    # Enhance the prompt for better video results
    enhanced_prompt = f"Cinematic slow-motion footage of {keyword}, high quality, dramatic lighting, 4K"
    
    return generator.generate_clip(enhanced_prompt, duration)


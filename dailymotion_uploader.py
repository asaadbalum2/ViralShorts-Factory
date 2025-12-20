#!/usr/bin/env python3
"""
ViralShorts Factory - Dailymotion Uploader
FULLY AUTONOMOUS video upload to Dailymotion.

=============================================================================
DAILYMOTION SHORTS SUPPORT - WHAT YOU NEED TO KNOW
=============================================================================

Q: Does Dailymotion have "Shorts" like YouTube/TikTok?
A: Sort of! Dailymotion supports vertical videos (9:16 aspect ratio) but doesn't
   have a dedicated "Shorts" section like YouTube. However:
   
   - Vertical videos ARE supported and play well on mobile
   - Short videos (< 60 seconds) work fine
   - They get good visibility on mobile app
   - Same content can be uploaded as YouTube/TikTok

Q: Should we upload the same content as YouTube?
A: YES! The same vertical short videos work on Dailymotion. Benefits:
   - More reach with same content
   - Dailymotion has ~400M monthly users
   - Lower competition than YouTube
   - Monetization available

Q: Daily upload limits?
A: Free tier: ~50 uploads per day (more than enough!)

=============================================================================
SETUP INSTRUCTIONS
=============================================================================

1. Create account at dailymotion.com
2. Go to: https://www.dailymotion.com/settings/developer
3. Create an API Key
4. Set GitHub Secrets:
   - DAILYMOTION_API_KEY (client ID)
   - DAILYMOTION_API_SECRET (client secret)
   - DAILYMOTION_USERNAME (your login email)
   - DAILYMOTION_PASSWORD (your password)

Note: API key and secret are already set! You just need to add:
- DAILYMOTION_USERNAME
- DAILYMOTION_PASSWORD
"""

import os
import requests
from typing import Optional, Dict
from pathlib import Path


def safe_print(msg: str):
    """Print with fallback for Windows encoding issues."""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Remove emojis for Windows compatibility
        import re
        clean = re.sub(r'[^\x00-\x7F]+', '', msg)
        print(clean)


class DailymotionUploader:
    """Upload videos to Dailymotion autonomously."""
    
    AUTH_URL = "https://api.dailymotion.com/oauth/token"
    UPLOAD_URL = "https://api.dailymotion.com/file/upload"
    VIDEO_URL = "https://api.dailymotion.com/me/videos"
    
    def __init__(self):
        self.api_key = os.environ.get("DAILYMOTION_API_KEY")
        self.api_secret = os.environ.get("DAILYMOTION_API_SECRET")
        self.username = os.environ.get("DAILYMOTION_USERNAME")
        self.password = os.environ.get("DAILYMOTION_PASSWORD")
        self.access_token = None
        
        self.is_configured = all([
            self.api_key, self.api_secret, self.username, self.password
        ])
    
    def authenticate(self) -> bool:
        """Get access token using password grant (required for uploads)."""
        if not self.is_configured:
            safe_print("[X] Dailymotion not configured")
            return False
        
        try:
            # Use password grant for user-level access (required for uploads)
            safe_print(f"[*] Authenticating with Dailymotion (user: {self.username})...")
            
            response = requests.post(self.AUTH_URL, data={
                "grant_type": "password",
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "username": self.username,
                "password": self.password,
                "scope": "manage_videos"
            }, timeout=30)
            
            data = response.json()
            
            if response.status_code == 200 and "access_token" in data:
                self.access_token = data["access_token"]
                safe_print(f"[OK] Dailymotion authenticated (token: {self.access_token[:15]}...)")
                return True
            else:
                error = data.get("error_description", data.get("error", "Unknown error"))
                safe_print(f"[X] Dailymotion auth failed: {error}")
                
                # If password grant fails, try client_credentials as test
                if "invalid_grant" in str(error).lower():
                    safe_print("[!] Username/password may be incorrect. Check DAILYMOTION_USERNAME and DAILYMOTION_PASSWORD secrets.")
                
                return False
                
        except requests.exceptions.Timeout:
            safe_print("[X] Dailymotion auth timeout")
            return False
        except Exception as e:
            safe_print(f"[X] Auth error: {e}")
            return False
    
    def upload_video(self, video_path: str, title: str, description: str,
                    tags: list = None, channel: str = "videogames") -> Optional[str]:
        """
        Upload video to Dailymotion.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            channel: Dailymotion channel category
            
        Returns:
            Video ID if successful, None otherwise
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"❌ Video not found: {video_path}")
            return None
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            # Step 1: Get upload URL
            print(f"📤 Getting upload URL...")
            response = requests.get(self.UPLOAD_URL, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get upload URL: {response.text}")
                return None
            
            upload_data = response.json()
            upload_url = upload_data.get("upload_url")
            
            # Step 2: Upload the file
            print(f"📤 Uploading {video_path.name}...")
            with open(video_path, "rb") as f:
                files = {"file": (video_path.name, f, "video/mp4")}
                response = requests.post(upload_url, files=files)
            
            if response.status_code != 200:
                print(f"❌ Upload failed: {response.text}")
                return None
            
            file_url = response.json().get("url")
            
            # Step 3: Create video entry
            print(f"📤 Creating video entry...")
            video_data = {
                "url": file_url,
                "title": title[:255],  # Dailymotion limit
                "description": description[:3000],
                "tags": ",".join(tags[:20]) if tags else "viral,shorts",
                "channel": channel,
                "published": "true",
                "is_created_for_kids": "false"
            }
            
            response = requests.post(
                self.VIDEO_URL,
                headers=headers,
                data=video_data
            )
            
            if response.status_code in [200, 201]:
                video_id = response.json().get("id")
                video_url = f"https://www.dailymotion.com/video/{video_id}"
                print(f"✅ Uploaded to Dailymotion: {video_url}")
                return video_id
            else:
                print(f"❌ Failed to create video: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def get_upload_limit_status(self) -> Dict:
        """Check daily upload limits."""
        if not self.access_token:
            if not self.authenticate():
                return {"error": "Not authenticated"}
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                "https://api.dailymotion.com/me?fields=limits",
                headers=headers
            )
            return response.json()
        except:
            return {"error": "Failed to get limits"}


def upload_to_dailymotion(video_path: str, title: str, 
                          description: str, tags: list = None) -> Optional[str]:
    """Convenience function for uploading."""
    uploader = DailymotionUploader()
    if uploader.is_configured:
        return uploader.upload_video(video_path, title, description, tags)
    else:
        print("⚠️ Dailymotion not configured. Set these env vars:")
        print("   DAILYMOTION_API_KEY")
        print("   DAILYMOTION_API_SECRET")
        print("   DAILYMOTION_USERNAME")
        print("   DAILYMOTION_PASSWORD")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("📺 Dailymotion Uploader - Setup Check")
    print("=" * 60)
    
    uploader = DailymotionUploader()
    
    if uploader.is_configured:
        print("✅ Dailymotion is configured!")
        if uploader.authenticate():
            limits = uploader.get_upload_limit_status()
            print(f"📊 Account limits: {limits}")
    else:
        print("""
❌ Dailymotion NOT configured

To set up:
1. Create account at dailymotion.com
2. Go to: https://www.dailymotion.com/settings/developer
3. Click "Create a new API key"
4. Set these environment variables:

   DAILYMOTION_API_KEY=your_key
   DAILYMOTION_API_SECRET=your_secret
   DAILYMOTION_USERNAME=your_email
   DAILYMOTION_PASSWORD=your_password

5. Add to GitHub Secrets for workflow automation
""")


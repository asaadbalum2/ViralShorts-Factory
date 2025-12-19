#!/usr/bin/env python3
"""
API Health Check System
Validates all API keys and reports status for dashboard.
Can auto-refresh tokens where possible.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path


class APIHealthChecker:
    """Check health of all API keys and services."""
    
    def __init__(self):
        self.results = {}
        self.output_path = Path("api_health_status.json")
    
    def check_groq(self) -> Tuple[bool, str]:
        """Check GROQ API key validity."""
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return False, "❌ GROQ_API_KEY not set"
        
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            # Simple test request
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Say 'test' in one word"}],
                max_tokens=5
            )
            return True, "✅ GROQ API working"
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "invalid" in error_msg.lower():
                return False, f"❌ GROQ API key INVALID - Get new key at https://console.groq.com/keys"
            return False, f"⚠️ GROQ error: {error_msg[:100]}"
    
    def check_gemini(self) -> Tuple[bool, str]:
        """Check Gemini API key validity."""
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return False, "❌ GEMINI_API_KEY not set"
        
        try:
            # Try new API first
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents="Say 'test' in one word"
                )
                return True, "✅ Gemini API working (new SDK)"
            except ImportError:
                pass
            
            # Fallback to old API
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Say 'test' in one word")
            return True, "✅ Gemini API working (legacy SDK)"
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg or "invalid" in error_msg.lower():
                return False, f"❌ Gemini API key INVALID - Get new key at https://aistudio.google.com/apikey"
            if "404" in error_msg:
                return False, f"⚠️ Gemini model not found - may need SDK update"
            return False, f"⚠️ Gemini error: {error_msg[:100]}"
    
    def check_pexels(self) -> Tuple[bool, str]:
        """Check Pexels API key validity."""
        api_key = os.environ.get("PEXELS_API_KEY", "")
        if not api_key:
            return False, "❌ PEXELS_API_KEY not set"
        
        try:
            headers = {"Authorization": api_key}
            response = requests.get(
                "https://api.pexels.com/v1/search?query=test&per_page=1",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return True, "✅ Pexels API working"
            elif response.status_code == 401:
                return False, "❌ Pexels API key INVALID - Get new key at https://www.pexels.com/api/"
            else:
                return False, f"⚠️ Pexels returned status {response.status_code}"
        except Exception as e:
            return False, f"⚠️ Pexels error: {str(e)[:100]}"
    
    def check_youtube(self) -> Tuple[bool, str]:
        """Check YouTube OAuth credentials validity."""
        client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
        client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        
        if not all([client_id, client_secret, refresh_token]):
            missing = []
            if not client_id: missing.append("CLIENT_ID")
            if not client_secret: missing.append("CLIENT_SECRET")
            if not refresh_token: missing.append("REFRESH_TOKEN")
            return False, f"❌ YouTube missing: {', '.join(missing)}"
        
        try:
            # Try to refresh the token
            response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "✅ YouTube OAuth working"
            else:
                error = response.json().get("error_description", response.text[:100])
                return False, f"❌ YouTube OAuth error: {error}"
        except Exception as e:
            return False, f"⚠️ YouTube check error: {str(e)[:100]}"
    
    def check_printful(self) -> Tuple[bool, str]:
        """Check Printful API key validity."""
        api_key = os.environ.get("PRINTFUL_API_KEY", "")
        if not api_key:
            return False, "⚠️ PRINTFUL_API_KEY not set (optional)"
        
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.printful.com/store",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                store_info = response.json().get("result", {})
                store_name = store_info.get("name", "Unknown")
                return True, f"✅ Printful working - Store: {store_name}"
            elif response.status_code == 401:
                return False, "❌ Printful API key INVALID - Get new key at https://www.printful.com/dashboard/settings/developers"
            else:
                return False, f"⚠️ Printful returned status {response.status_code}"
        except Exception as e:
            return False, f"⚠️ Printful error: {str(e)[:100]}"
    
    def check_huggingface(self) -> Tuple[bool, str]:
        """Check HuggingFace API token validity."""
        token = os.environ.get("HF_TOKEN", "")
        if not token:
            return False, "⚠️ HF_TOKEN not set (needed for TrendMerch)"
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://huggingface.co/api/whoami",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                user = response.json().get("name", "Unknown")
                return True, f"✅ HuggingFace working - User: {user}"
            else:
                return False, "❌ HF_TOKEN INVALID - Get new token at https://huggingface.co/settings/tokens"
        except Exception as e:
            return False, f"⚠️ HuggingFace error: {str(e)[:100]}"
    
    def run_all_checks(self) -> Dict:
        """Run all API health checks."""
        print("\n🔍 Running API Health Checks...\n")
        
        checks = [
            ("GROQ", self.check_groq),
            ("Gemini", self.check_gemini),
            ("Pexels", self.check_pexels),
            ("YouTube", self.check_youtube),
            ("Printful", self.check_printful),
            ("HuggingFace", self.check_huggingface),
        ]
        
        all_healthy = True
        critical_issues = []
        
        for name, check_func in checks:
            try:
                is_healthy, message = check_func()
                self.results[name] = {
                    "healthy": is_healthy,
                    "message": message,
                    "checked_at": datetime.now().isoformat()
                }
                print(f"  {name}: {message}")
                
                if not is_healthy and "INVALID" in message:
                    all_healthy = False
                    critical_issues.append(f"{name}: {message}")
            except Exception as e:
                self.results[name] = {
                    "healthy": False,
                    "message": f"❌ Check failed: {str(e)[:100]}",
                    "checked_at": datetime.now().isoformat()
                }
                print(f"  {name}: ❌ Check failed: {e}")
        
        # Summary
        summary = {
            "all_healthy": all_healthy,
            "checked_at": datetime.now().isoformat(),
            "critical_issues": critical_issues,
            "services": self.results
        }
        
        # Save to file for dashboard
        with open(self.output_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Results saved to {self.output_path}")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES REQUIRING ATTENTION:")
            for issue in critical_issues:
                print(f"   • {issue}")
        
        return summary


def main():
    """Run health checks and output status."""
    checker = APIHealthChecker()
    results = checker.run_all_checks()
    
    # Exit with error if critical issues
    if not results["all_healthy"]:
        print("\n⚠️ Some services have issues - check dashboard for details")
        # Don't exit with error - just warn
    
    return results


if __name__ == "__main__":
    main()


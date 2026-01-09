#!/usr/bin/env python3
"""
Workflow Analyzer - Comprehensive analysis of scheduled workflow runs.

Usage:
    python scripts/analyze_workflows.py --days 1    # Last 24 hours
    python scripts/analyze_workflows.py --days 2    # Last 48 hours
    python scripts/analyze_workflows.py --days 7    # Last week

Analyzes:
1. ViralShorts Factory - Auto Video Generator
2. Pre-Work Data Fetcher
3. Weekly Analytics Feedback
4. Monthly Viral Analysis

Reports:
- Workflow pass/fail status
- Expected behavior verification
- Persistent data read/write success
- Quota usage per workflow
- Video characteristics and scores
"""

import argparse
import subprocess
import json
import re
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class WorkflowRun:
    """Represents a single workflow run."""
    run_id: int
    name: str
    status: str
    conclusion: str
    created_at: datetime
    event: str
    log_content: str = ""
    analysis: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VideoInfo:
    """Extracted video characteristics."""
    title: str = ""
    topic: str = ""
    category: str = ""
    duration: float = 0
    phrase_count: int = 0
    words_per_phrase: int = 0
    hook: str = ""
    hook_type: str = ""
    music_mood: str = ""
    voice_style: str = ""
    virality_score: float = 0
    engagement_score: float = 0
    retention_score: float = 0
    script_score: float = 0
    quality_gate_passed: bool = False
    quality_gate_reason: str = ""
    uploaded: bool = False
    platform: str = ""
    video_id: str = ""
    youtube_url: str = ""
    file_size_mb: float = 0
    generation_time_sec: float = 0
    ai_model_used: str = ""
    tts_engine: str = ""
    b_roll_count: int = 0

@dataclass
class QuotaUsage:
    """Quota usage for a workflow."""
    provider: str
    endpoint: str
    calls: int
    model: str = ""
    daily_limit: int = 0  # 0 means unlimited/unknown
    percent_used: float = 0.0
    limit_reached: bool = False
    error_429: bool = False
    
@dataclass
class PersistentDataAnalysis:
    """Analysis of persistent data files."""
    file_name: str
    exists: bool = False
    size_bytes: int = 0
    last_modified: str = ""
    key_fields: Dict[str, Any] = field(default_factory=dict)
    record_count: int = 0
    health_status: str = "unknown"  # healthy, stale, empty, corrupted

@dataclass
class WorkflowAnalysisResult:
    """Complete analysis result for a workflow run."""
    run: WorkflowRun
    passed: bool = False
    expected_behavior_met: bool = False
    persistent_read_success: bool = False
    persistent_write_success: bool = False
    videos: List[VideoInfo] = field(default_factory=list)
    quota_usage: List[QuotaUsage] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    key_metrics: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# KNOWN QUOTA LIMITS (requests per day)
# ============================================================
QUOTA_LIMITS = {
    "GEMINI": {
        "gemini-2.0-flash": 1500,
        "gemini-1.5-flash": 1500,
        "gemini-1.5-pro": 50,
        "gemini-2.0-flash-lite": 1500,
        "generateContent": 1500,  # Default Flash
        "/models (FREE)": float('inf'),
    },
    "GROQ": {
        "llama-3.3-70b-versatile": 1000,
        "llama-3.1-8b-instant": 1000,
        "chat/completions": 1000,
    },
    "OPENROUTER": {
        "chat/completions": 200,  # Free tier
    },
    "PEXELS": {
        "videos/search": 200,
    },
    "YOUTUBE": {
        "v3/various": 10000,  # Units, not calls
        "upload": 6,  # Videos per day
    },
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_print(msg: str):
    """Print with encoding safety."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode())


def run_gh_command(args: List[str], timeout: int = 60, max_output_mb: int = 5) -> Optional[str]:
    """Run a GitHub CLI command and return output with safety limits."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            output = result.stdout
            # Limit output size to prevent memory/connection issues
            max_chars = max_output_mb * 1024 * 1024
            if len(output) > max_chars:
                safe_print(f"      [WARN] Truncating output from {len(output)//1024}KB to {max_output_mb}MB")
                output = output[:max_chars]
            return output
        else:
            safe_print(f"[WARN] gh command failed: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        safe_print(f"[WARN] gh command timed out after {timeout}s")
        return None
    except MemoryError:
        safe_print(f"[WARN] gh command output too large - skipping")
        return None
    except Exception as e:
        safe_print(f"[ERROR] gh command error: {e}")
        return None


def get_scheduled_runs(days: int) -> List[WorkflowRun]:
    """Get all scheduled workflow runs from the last N days."""
    safe_print(f"\n[1/6] Fetching scheduled workflow runs from last {days} day(s)...")
    
    # Calculate how many runs to fetch (rough estimate: 6 video + 1 prework + 0-1 analytics per day)
    limit = max(50, days * 10)
    
    output = run_gh_command([
        "run", "list", 
        "--limit", str(limit),
        "--json", "databaseId,name,status,conclusion,createdAt,event"
    ], timeout=30)
    
    if not output:
        safe_print("[ERROR] Failed to fetch workflow runs")
        return []
    
    try:
        runs_data = json.loads(output)
    except json.JSONDecodeError:
        safe_print("[ERROR] Failed to parse workflow runs JSON")
        return []
    
    cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    scheduled_runs = []
    
    for run in runs_data:
        # Only include scheduled runs
        if run.get("event") != "schedule":
            continue
        
        created_at = datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00")).replace(tzinfo=None)
        
        if created_at < cutoff_date:
            continue
        
        scheduled_runs.append(WorkflowRun(
            run_id=run["databaseId"],
            name=run["name"],
            status=run["status"],
            conclusion=run.get("conclusion", "unknown"),
            created_at=created_at,
            event=run["event"]
        ))
    
    safe_print(f"   Found {len(scheduled_runs)} scheduled runs in the last {days} day(s)")
    
    # Group by workflow type for display
    by_type = {}
    for run in scheduled_runs:
        by_type.setdefault(run.name, []).append(run)
    
    for wf_name, runs in by_type.items():
        safe_print(f"   - {wf_name}: {len(runs)} runs")
    
    return scheduled_runs


def download_log_in_batches(run_id: int, batch_size: int = 50000) -> str:
    """Download workflow log with safety limits to avoid connection loss."""
    safe_print(f"      Downloading log for run {run_id}...")
    
    try:
        # Use shorter timeout and limit output size
        output = run_gh_command([
            "run", "view", str(run_id), "--log"
        ], timeout=90, max_output_mb=3)
        
        if not output:
            # Try downloading failed logs only (smaller)
            safe_print(f"      Retrying with --log-failed...")
            output = run_gh_command([
                "run", "view", str(run_id), "--log-failed"
            ], timeout=60, max_output_mb=2)
        
        if output:
            lines = output.split('\n')
            safe_print(f"      Downloaded {len(lines)} lines ({len(output)//1024}KB)")
            return output
        
        return ""
    except Exception as e:
        safe_print(f"      [ERROR] Failed to download log: {e}")
        return ""


# ============================================================
# KNOWN QUOTA LIMITS (requests per day)
# ============================================================
QUOTA_LIMITS = {
    "GEMINI": {
        "gemini-2.0-flash": 1500,
        "gemini-1.5-flash": 1500,
        "gemini-1.5-pro": 50,
        "gemini-2.0-flash-lite": 1500,
        "generateContent": 1500,  # Default Flash
        "/models (FREE)": float('inf'),
    },
    "GROQ": {
        "llama-3.3-70b-versatile": 1000,
        "llama-3.1-8b-instant": 1000,
        "chat/completions": 1000,
    },
    "OPENROUTER": {
        "chat/completions": 200,  # Free tier
    },
    "PEXELS": {
        "videos/search": 200,
    },
    "YOUTUBE": {
        "v3/various": 10000,  # Units, not calls
        "upload": 6,  # Videos per day
    },
}


# ============================================================
# PERSISTENT DATA ANALYZER
# ============================================================

def download_persistent_data() -> Dict[str, PersistentDataAnalysis]:
    """Download and analyze persistent data files from the latest artifact."""
    safe_print("\n[PERSISTENT DATA] Downloading latest persistent-state artifact...")
    
    results = {}
    
    # Download artifact using gh run download
    import tempfile
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        import subprocess
        subprocess.run([
            "gh", "run", "download", "--name", "persistent-state", "-D", str(temp_dir)
        ], capture_output=True, timeout=60)
        
        # Analyze each file
        persistent_files = [
            "variety_state.json",
            "viral_patterns.json",
            "analytics_state.json",
            "upload_state.json",
            "quota_cache.json",
            "hook_word_performance.json",
            "category_decay.json",
            "series_state.json",
            "schedule_advisor.json",
            "learned_video_metrics.json",
        ]
        
        for file_name in persistent_files:
            file_path = temp_dir / file_name
            analysis = PersistentDataAnalysis(file_name=file_name)
            
            if file_path.exists():
                analysis.exists = True
                analysis.size_bytes = file_path.stat().st_size
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract key fields based on file type
                    if file_name == "variety_state.json":
                        analysis.key_fields = {
                            "preferred_categories": data.get("preferred_categories", [])[:3],
                            "last_feedback": data.get("last_feedback", "N/A"),
                            "recent_topics_count": len(data.get("recent_topics", [])),
                        }
                        analysis.health_status = "healthy" if data.get("last_feedback") else "stale"
                        
                    elif file_name == "viral_patterns.json":
                        analysis.key_fields = {
                            "best_patterns_count": len(data.get("our_best_patterns", [])),
                            "key_insight": data.get("key_insight", "N/A")[:50] if data.get("key_insight") else "N/A",
                            "optimal_duration": data.get("optimal_duration"),
                            "last_update": data.get("last_performance_update", "N/A"),
                        }
                        analysis.health_status = "healthy" if data.get("last_performance_update") else "stale"
                        
                    elif file_name == "analytics_state.json":
                        analysis.key_fields = {
                            "videos_tracked": len(data.get("videos", [])),
                            "total_views": data.get("total_views", 0),
                            "avg_views": round(data.get("avg_views", 0), 1),
                            "last_updated": data.get("last_updated", "N/A"),
                        }
                        analysis.record_count = len(data.get("videos", []))
                        analysis.health_status = "healthy" if data.get("last_updated") else "stale"
                        
                    elif file_name == "upload_state.json":
                        analysis.key_fields = {
                            "total_uploads": data.get("total_uploads", 0),
                            "youtube_uploads": data.get("youtube_uploads", 0),
                            "last_upload": data.get("last_upload_time", "N/A"),
                        }
                        analysis.health_status = "healthy"
                        
                    elif file_name == "quota_cache.json":
                        analysis.key_fields = {
                            "providers_cached": list(data.keys())[:3],
                            "cache_entries": len(data),
                        }
                        analysis.health_status = "healthy" if data else "empty"
                        
                    elif file_name == "learned_video_metrics.json":
                        analysis.key_fields = {
                            "videos_learned_from": len(data.get("video_performances", {})),
                            "optimal_duration": data.get("optimal_duration"),
                            "optimal_phrases": data.get("optimal_phrase_count"),
                        }
                        analysis.health_status = "healthy" if data.get("video_performances") else "empty"
                        
                    else:
                        # Generic analysis
                        analysis.key_fields = {"keys": list(data.keys())[:5]}
                        analysis.health_status = "healthy" if data else "empty"
                        
                except json.JSONDecodeError:
                    analysis.health_status = "corrupted"
                except Exception as e:
                    analysis.health_status = f"error: {str(e)[:30]}"
            else:
                analysis.health_status = "missing"
            
            results[file_name] = analysis
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        safe_print(f"   [ERROR] Failed to download/analyze persistent data: {e}")
    
    return results


def extract_video_details(log: str) -> List[VideoInfo]:
    """Extract detailed video characteristics from log."""
    videos = []
    
    # Find video file mentions - use unique set to avoid duplicates
    video_files = set(re.findall(r'output/(pro_[^\s]+\.mp4)', log))
    
    for vf in video_files:
        video = VideoInfo(title=vf)
        
        # Extract category from filename (pro_CATEGORY_ID.mp4)
        cat_match = re.search(r'pro_([^_]+)_', vf)
        if cat_match:
            video.category = cat_match.group(1)
        
        # Try to get size
        size_match = re.search(rf'{re.escape(vf)}\s*\((\d+)MB\)', log)
        if size_match:
            video.file_size_mb = float(size_match.group(1))
        
        # Extract scores from log
        # Virality score
        virality_match = re.search(r'[Vv]irality[_\s]?[Ss]core[:\s]*([\d.]+)', log)
        if virality_match:
            video.virality_score = float(virality_match.group(1))
        
        # Engagement score
        engage_match = re.search(r'[Ee]ngagement[_\s]?[Ss]core[:\s]*([\d.]+)', log)
        if engage_match:
            video.engagement_score = float(engage_match.group(1))
        
        # Retention score
        retain_match = re.search(r'[Rr]etention[_\s]?[Ss]core[:\s]*([\d.]+)', log)
        if retain_match:
            video.retention_score = float(retain_match.group(1))
        
        # Script score
        script_match = re.search(r'[Ss]cript[_\s]?[Ss]core[:\s]*([\d.]+)', log)
        if script_match:
            video.script_score = float(script_match.group(1))
        
        # Quality gate
        if "Quality Gate: PASSED" in log or "quality_gate.*passed" in log.lower():
            video.quality_gate_passed = True
        gate_match = re.search(r'[Qq]uality[_\s]?[Gg]ate[:\s]*(PASSED|FAILED)(?:[:\s]*(.+?))?[\n\r]', log)
        if gate_match:
            video.quality_gate_passed = gate_match.group(1) == "PASSED"
            video.quality_gate_reason = gate_match.group(2) or ""
        
        # Duration
        dur_match = re.search(r'[Dd]uration[:\s]*([\d.]+)\s*(?:s|sec)', log)
        if dur_match:
            video.duration = float(dur_match.group(1))
        
        # Phrase count
        phrase_match = re.search(r'(\d+)\s*phrases?', log)
        if phrase_match:
            video.phrase_count = int(phrase_match.group(1))
        
        # Hook - look for actual content hooks, not filenames
        hook_patterns = [
            r'\[HOOK\][:\s]*"([^"]+)"',
            r'Hook[:\s]*"([^"]+)"',
            r'hook_text[:\s]*["\']([^"\']+)["\']',
        ]
        for pattern in hook_patterns:
            hook_match = re.search(pattern, log, re.IGNORECASE)
            if hook_match and not hook_match.group(1).endswith('.json'):
                video.hook = hook_match.group(1)[:50]
                break
        
        # AI Model used
        model_match = re.search(r'(?:Using|Model)[:\s]*(gemini-[^\s,]+|llama[^\s,]+|gpt[^\s,]+)', log, re.IGNORECASE)
        if model_match:
            video.ai_model_used = model_match.group(1)
        
        # TTS Engine
        if "edge-tts" in log.lower():
            video.tts_engine = "Edge-TTS"
        elif "gtts" in log.lower():
            video.tts_engine = "gTTS"
        
        # YouTube URL
        yt_match = re.search(r'youtube\.com/shorts/([a-zA-Z0-9_-]+)', log)
        if yt_match:
            video.video_id = yt_match.group(1)
            video.youtube_url = f"https://youtube.com/shorts/{video.video_id}"
        
        # Upload status
        upload_patterns = [
            "Successfully uploaded to YouTube",
            "Upload complete",
            "[YOUTUBE] Uploading:",
            "[UPLOAD] Title:"
        ]
        if any(pattern in log for pattern in upload_patterns):
            video.uploaded = True
            video.platform = "YouTube"
        
        # B-roll count
        broll_match = re.search(r'(\d+)\s*(?:b-?roll|video\s*clips?)', log, re.IGNORECASE)
        if broll_match:
            video.b_roll_count = int(broll_match.group(1))
        
        videos.append(video)
    
    return videos


def extract_detailed_quota(log: str, workflow_name: str) -> List[QuotaUsage]:
    """Extract detailed quota usage with model-level breakdown and percentages."""
    quota_list = []
    
    # Gemini - look for specific model usage
    gemini_models = re.findall(r'(?:Using|Model|model)[:\s]*(gemini-[^\s,\]]+)', log, re.IGNORECASE)
    gemini_model_counts = {}
    for model in gemini_models:
        model_clean = model.lower().strip()
        gemini_model_counts[model_clean] = gemini_model_counts.get(model_clean, 0) + 1
    
    # Also count generateContent calls
    generate_calls = len(re.findall(r'generateContent', log))
    if generate_calls > 0 and not gemini_model_counts:
        gemini_model_counts["generateContent"] = generate_calls
    
    for model, calls in gemini_model_counts.items():
        limit = QUOTA_LIMITS["GEMINI"].get(model, QUOTA_LIMITS["GEMINI"].get("generateContent", 1500))
        percent = (calls / limit * 100) if limit != float('inf') else 0
        quota_list.append(QuotaUsage(
            provider="GEMINI",
            endpoint=model,
            calls=calls,
            model=model,
            daily_limit=int(limit) if limit != float('inf') else 0,
            percent_used=round(percent, 2)
        ))
    
    # Groq
    groq_models = re.findall(r'(?:llama-[^\s,\]]+|mixtral[^\s,\]]+)', log, re.IGNORECASE)
    groq_model_counts = {}
    for model in groq_models:
        model_clean = model.lower().strip()
        groq_model_counts[model_clean] = groq_model_counts.get(model_clean, 0) + 1
    
    groq_calls = len(re.findall(r'api\.groq\.com/openai/v1/chat', log))
    if groq_calls > 0 and not groq_model_counts:
        groq_model_counts["chat/completions"] = groq_calls
    
    for model, calls in groq_model_counts.items():
        limit = QUOTA_LIMITS["GROQ"].get(model, 1000)
        percent = (calls / limit * 100)
        quota_list.append(QuotaUsage(
            provider="GROQ",
            endpoint=model,
            calls=calls,
            model=model,
            daily_limit=int(limit),
            percent_used=round(percent, 2)
        ))
    
    # OpenRouter
    openrouter_calls = len(re.findall(r'openrouter\.ai/api/v1/chat', log))
    if openrouter_calls > 0:
        limit = QUOTA_LIMITS["OPENROUTER"]["chat/completions"]
        quota_list.append(QuotaUsage(
            provider="OPENROUTER",
            endpoint="chat/completions",
            calls=openrouter_calls,
            daily_limit=limit,
            percent_used=round(openrouter_calls / limit * 100, 2)
        ))
    
    # Pexels
    pexels_calls = len(re.findall(r'api\.pexels\.com/videos', log))
    if pexels_calls > 0:
        limit = QUOTA_LIMITS["PEXELS"]["videos/search"]
        quota_list.append(QuotaUsage(
            provider="PEXELS",
            endpoint="videos/search",
            calls=pexels_calls,
            daily_limit=limit,
            percent_used=round(pexels_calls / limit * 100, 2)
        ))
    
    # YouTube
    youtube_calls = len(re.findall(r'googleapis\.com/youtube/v3', log))
    youtube_uploads = len(re.findall(r'\[YOUTUBE\] Uploading:', log))
    
    if youtube_calls > 0:
        quota_list.append(QuotaUsage(
            provider="YOUTUBE",
            endpoint="v3/api_calls",
            calls=youtube_calls,
            daily_limit=10000,
            percent_used=round(youtube_calls / 10000 * 100, 2)
        ))
    
    if youtube_uploads > 0:
        # NOTE: YouTube limit is 6 per DAY. This shows per-RUN percentage.
        # For multi-day analysis, the report aggregates by DAY, not total.
        quota_list.append(QuotaUsage(
            provider="YOUTUBE",
            endpoint="uploads",
            calls=youtube_uploads,
            daily_limit=6,
            percent_used=round(youtube_uploads / 6 * 100, 2),  # Per-run: 1 upload = ~17%
        ))
    
    # Check for 429 errors
    if "429" in log or "rate limit" in log.lower() or "quota" in log.lower():
        for q in quota_list:
            pattern = rf'({q.provider}|{q.provider.lower()})[^\n]*?(429|rate.?limit|quota.?exhaust)'
            if re.search(pattern, log, re.IGNORECASE):
                q.error_429 = True
                q.limit_reached = True
    
    return quota_list


# ============================================================
# WORKFLOW ANALYZERS (One per workflow type)
# ============================================================

def analyze_video_generator(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    """Analyze ViralShorts Factory - Auto Video Generator run."""
    result = WorkflowAnalysisResult(run=run)
    
    # Check if passed
    result.passed = run.conclusion == "success"
    
    # Check persistent data read - what files were read
    persistent_read_files = []
    if "Restored patterns from artifact" in log or "[OK] Restored" in log:
        result.persistent_read_success = True
        persistent_read_files.append("persistent-state (artifact)")
    if "variety_state" in log:
        persistent_read_files.append("variety_state.json")
    if "viral_patterns" in log:
        persistent_read_files.append("viral_patterns.json")
    if "upload_state" in log:
        persistent_read_files.append("upload_state.json")
    
    if "No previous state found" in log:
        result.persistent_read_success = True  # Valid - fresh start
        result.warnings.append("Fresh state (no previous persistent data)")
    
    result.key_metrics["persistent_files_read"] = persistent_read_files
    
    # Check persistent data write - what files were written
    persistent_write_files = []
    if "persistent-state" in log and ("Artifact name is valid" in log or "successfully uploaded" in log.lower()):
        result.persistent_write_success = True
        persistent_write_files.append("persistent-state (artifact)")
    
    # Check for specific file saves
    for fname in ["variety_state", "viral_patterns", "upload_state", "analytics_state", "learned_video_metrics"]:
        if f"Saved {fname}" in log or f"Updated {fname}" in log or f"{fname}.json" in log:
            persistent_write_files.append(f"{fname}.json")
    
    result.key_metrics["persistent_files_written"] = persistent_write_files
    
    # Check pre-generated concepts loaded
    if "Loaded" in log and "pre-generated concepts" in log:
        match = re.search(r'Loaded (\d+) pre-generated concepts', log)
        if match:
            result.key_metrics["prework_concepts_used"] = int(match.group(1))
    
    # Extract detailed video information
    result.videos = extract_video_details(log)
    
    # Check expected behavior
    if result.passed and len(result.videos) > 0:
        if result.videos[0].uploaded or "no-upload" in log.lower() or "test mode" in log.lower():
            result.expected_behavior_met = True
    
    # Extract detailed quota usage
    result.quota_usage = extract_detailed_quota(log, run.name)
    
    # Check for errors
    if "CRITICAL" in log and "No videos were generated" in log and len(result.videos) == 0:
        result.errors.append("No videos were generated")
    elif "CRITICAL" in log:
        errors = re.findall(r'CRITICAL[:\s]+([^\n\[]+)', log)
        clean_errors = list(set(
            e.strip() for e in errors 
            if e.strip() 
            and not e.startswith('[0m')
            and not (len(result.videos) > 0 and "No videos" in e)
        ))
        result.errors.extend(clean_errors[:5])
    
    # Extract generation timing
    gen_time_match = re.search(r'(?:Generation|Total)[^\d]*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)', log)
    if gen_time_match:
        result.key_metrics["generation_time_sec"] = float(gen_time_match.group(1))
    
    # Extract AI model used
    model_match = re.search(r'(?:Using|Selected|Model)[:\s]*(gemini-[^\s,\]]+)', log, re.IGNORECASE)
    if model_match:
        result.key_metrics["ai_model"] = model_match.group(1)
    
    # Check for quality gate results
    if "Quality Gate: PASSED" in log:
        result.key_metrics["quality_gate"] = "PASSED"
    elif "Quality Gate: FAILED" in log:
        result.key_metrics["quality_gate"] = "FAILED"
    
    return result


def analyze_prework_fetcher(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    """Analyze Pre-Work Data Fetcher run."""
    result = WorkflowAnalysisResult(run=run)
    
    result.passed = run.conclusion == "success"
    
    # Check if concepts were generated
    concepts_match = re.search(r'Concepts generated:\s*(\d+)', log)
    if concepts_match:
        result.key_metrics["concepts_generated"] = int(concepts_match.group(1))
        result.expected_behavior_met = True
    
    # Check artifact upload
    if "pre-generated-concepts" in log and "Artifact name is valid" in log:
        result.persistent_write_success = True
    
    # Check git commit
    if "Pre-work: Generated" in log or "No changes to commit" in log:
        result.key_metrics["git_committed"] = True
    
    # Extract quota usage
    result.quota_usage = extract_detailed_quota(log, run.name)
    
    # Check for rate limit skip - but this shouldn't show as warning if concepts were generated
    if ("QUOTA EXHAUSTED" in log or "exit 78" in log) and result.key_metrics.get("concepts_generated", 0) == 0:
        result.warnings.append("Skipped due to quota exhaustion (will retry next schedule)")
        result.expected_behavior_met = True  # This is expected behavior
    
    return result


def analyze_analytics_feedback(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    """Analyze Weekly Analytics Feedback run."""
    result = WorkflowAnalysisResult(run=run)
    
    result.passed = run.conclusion == "success"
    
    # Check if YouTube data was fetched
    if "Found" in log and "videos" in log:
        match = re.search(r'Found (\d+) videos', log)
        if match:
            result.key_metrics["videos_analyzed"] = int(match.group(1))
            result.expected_behavior_met = True
    
    # Check persistent state restored
    if "[OK] Restored state" in log:
        result.persistent_read_success = True
    
    # Check persistent state saved
    if "persistent-state" in log:
        result.persistent_write_success = True
    
    # Check AI analysis
    if "Key insight:" in log:
        insight_match = re.search(r'Key insight:\s*([^\n]+)', log)
        if insight_match:
            result.key_metrics["ai_insight"] = insight_match.group(1)[:100]
    
    # Check pattern updates
    pattern_updates = [
        "variety_state.json updated",
        "viral_patterns.json updated",
        "hook_word_performance.json updated",
        "category_decay.json updated"
    ]
    updates_found = sum(1 for p in pattern_updates if p in log)
    result.key_metrics["pattern_files_updated"] = updates_found
    
    # Check shadow-ban status
    if "Status: concerning" in log:
        result.warnings.append("Shadow-ban indicator detected!")
    elif "Status: normal" in log:
        result.key_metrics["shadow_ban_status"] = "normal"
    
    # Check for schedule skip
    if "AI recommends skipping" in log:
        result.key_metrics["skipped_by_ai"] = True
        result.expected_behavior_met = True  # Expected when not enough new videos
    
    # Extract quota usage
    result.quota_usage = extract_detailed_quota(log, run.name)
    
    return result


def analyze_monthly_analysis(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    """Analyze Monthly Viral Analysis run."""
    result = WorkflowAnalysisResult(run=run)
    
    result.passed = run.conclusion == "success"
    
    # Check if analysis ran
    if "Monthly Viral Analysis" in log or "analyze_viral_channels" in log:
        result.expected_behavior_met = True
    
    # Check persistent state
    if "[OK] Restored state" in log:
        result.persistent_read_success = True
    
    if "persistent-state" in log:
        result.persistent_write_success = True
    
    # Extract quota usage
    result.quota_usage = extract_detailed_quota(log, run.name)
    
    return result


def extract_quota_usage(log: str) -> List[QuotaUsage]:
    """Extract quota usage information from log."""
    quota_list = []
    
    # Gemini API calls (count actual API requests, not just URL mentions)
    gemini_generate = len(re.findall(r'generateContent', log))
    gemini_models = len(re.findall(r'/v1beta/models[^/]', log))
    if gemini_generate > 0:
        quota_list.append(QuotaUsage(
            provider="GEMINI",
            endpoint="generateContent",
            calls=gemini_generate
        ))
    if gemini_models > 0:
        quota_list.append(QuotaUsage(
            provider="GEMINI",
            endpoint="/models (FREE)",
            calls=gemini_models
        ))
    
    # Groq API calls
    groq_calls = len(re.findall(r'api\.groq\.com/openai/v1/chat', log))
    if groq_calls > 0:
        quota_list.append(QuotaUsage(
            provider="GROQ",
            endpoint="chat/completions",
            calls=groq_calls
        ))
    
    # OpenRouter calls
    openrouter_calls = len(re.findall(r'openrouter\.ai/api/v1/chat', log))
    if openrouter_calls > 0:
        quota_list.append(QuotaUsage(
            provider="OPENROUTER",
            endpoint="chat/completions",
            calls=openrouter_calls
        ))
    
    # Pexels calls
    pexels_calls = len(re.findall(r'api\.pexels\.com/videos', log))
    if pexels_calls > 0:
        quota_list.append(QuotaUsage(
            provider="PEXELS",
            endpoint="videos/search",
            calls=pexels_calls
        ))
    
    # YouTube API calls
    youtube_calls = len(re.findall(r'googleapis\.com/youtube/v3', log))
    if youtube_calls > 0:
        quota_list.append(QuotaUsage(
            provider="YOUTUBE",
            endpoint="v3/various",
            calls=youtube_calls
        ))
    
    # Check for 429 errors - look for specific patterns
    rate_limit_429 = False
    if "429" in log or "rate limit" in log.lower() or "quota" in log.lower():
        # Check for specific provider rate limits
        for provider in ["GEMINI", "GROQ", "OPENROUTER", "PEXELS", "YOUTUBE"]:
            pattern = rf'({provider}|{provider.lower()})[^\n]*?(429|rate.?limit|quota.?exhaust)'
            if re.search(pattern, log, re.IGNORECASE):
                for q in quota_list:
                    if q.provider == provider:
                        q.error_429 = True
                        q.limit_reached = True
                        rate_limit_429 = True
        
        # Also check for generic 429 near API calls
        if not rate_limit_429 and "HTTP 429" in log:
            # Try to identify which provider
            for q in quota_list:
                if q.calls > 5:  # Likely the one hitting limits
                    q.error_429 = True
                    q.limit_reached = True
    
    return quota_list


# ============================================================
# MAIN ANALYSIS ENGINE
# ============================================================

def analyze_workflow_run(run: WorkflowRun) -> WorkflowAnalysisResult:
    """Analyze a single workflow run based on its type."""
    
    # Download log
    log = download_log_in_batches(run.run_id)
    run.log_content = log
    
    if not log:
        result = WorkflowAnalysisResult(run=run)
        result.errors.append("Failed to download log")
        return result
    
    # Route to appropriate analyzer
    if "Auto Video Generator" in run.name:
        return analyze_video_generator(log, run)
    elif "Pre-Work" in run.name:
        return analyze_prework_fetcher(log, run)
    elif "Analytics Feedback" in run.name or "Weekly" in run.name:
        return analyze_analytics_feedback(log, run)
    elif "Monthly" in run.name or "Viral Analysis" in run.name:
        return analyze_monthly_analysis(log, run)
    else:
        result = WorkflowAnalysisResult(run=run)
        result.warnings.append(f"Unknown workflow type: {run.name}")
        return result


def generate_report(results: List[WorkflowAnalysisResult], days: int, persistent_data: Dict[str, PersistentDataAnalysis] = None):
    """Generate comprehensive analysis report."""
    
    safe_print("\n" + "=" * 90)
    safe_print("  COMPREHENSIVE WORKFLOW ANALYSIS REPORT")
    safe_print(f"  Period: Last {days} day(s)")
    safe_print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    safe_print("=" * 90)
    
    # Group by workflow type
    by_type: Dict[str, List[WorkflowAnalysisResult]] = {}
    for r in results:
        by_type.setdefault(r.run.name, []).append(r)
    
    # ============================================================
    # SECTION 1: Summary Table
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  1. WORKFLOW SUMMARY")
    safe_print("-" * 80)
    
    safe_print(f"\n   {'Workflow':<45} | {'Runs':>5} | {'Pass':>5} | {'Fail':>5} | {'Rate':>6}")
    safe_print("   " + "-" * 75)
    
    total_runs = 0
    total_passed = 0
    
    for wf_name, wf_results in by_type.items():
        runs = len(wf_results)
        passed = sum(1 for r in wf_results if r.passed)
        failed = runs - passed
        rate = f"{(passed/runs*100):.0f}%" if runs > 0 else "N/A"
        
        total_runs += runs
        total_passed += passed
        
        status_icon = "✅" if passed == runs else "⚠️" if passed > 0 else "❌"
        safe_print(f"   {status_icon} {wf_name[:43]:<43} | {runs:>5} | {passed:>5} | {failed:>5} | {rate:>6}")
    
    safe_print("   " + "-" * 75)
    overall_rate = f"{(total_passed/total_runs*100):.0f}%" if total_runs > 0 else "N/A"
    safe_print(f"   {'TOTAL':<45} | {total_runs:>5} | {total_passed:>5} | {total_runs-total_passed:>5} | {overall_rate:>6}")
    
    # ============================================================
    # SECTION 2: Detailed Status by Workflow Type
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  2. DETAILED STATUS BY WORKFLOW TYPE")
    safe_print("-" * 80)
    
    for wf_name, wf_results in by_type.items():
        safe_print(f"\n   📋 {wf_name}")
        safe_print("   " + "-" * 60)
        
        for r in sorted(wf_results, key=lambda x: x.run.created_at, reverse=True):
            status = "✅ PASS" if r.passed else "❌ FAIL"
            time_str = r.run.created_at.strftime("%Y-%m-%d %H:%M")
            
            safe_print(f"      {status} | {time_str} | Run #{r.run.run_id}")
            
            # Show key metrics
            if r.key_metrics:
                for key, val in list(r.key_metrics.items())[:3]:
                    safe_print(f"         → {key}: {val}")
            
            # Show videos if any
            if r.videos:
                for v in r.videos:
                    upload_status = "📤 Uploaded" if v.uploaded else "📁 Generated"
                    safe_print(f"         → Video: {v.title[:40]} ({v.file_size_mb}MB) {upload_status}")
            
            # Show errors
            for err in r.errors[:2]:
                safe_print(f"         ⚠️ Error: {err[:60]}")
            
            # Show warnings
            for warn in r.warnings[:2]:
                safe_print(f"         ℹ️ {warn[:60]}")
    
    # ============================================================
    # SECTION 3: Expected Behavior Verification
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  3. EXPECTED BEHAVIOR VERIFICATION")
    safe_print("-" * 80)
    
    behavior_checks = {
        "Auto Video Generator": [
            ("Generate video", lambda r: len(r.videos) > 0),
            ("Upload to YouTube", lambda r: any(v.uploaded for v in r.videos) or "no-upload" in str(r.run.log_content).lower()),
            ("Read persistent state", lambda r: r.persistent_read_success),
            ("Write persistent state", lambda r: r.persistent_write_success),
        ],
        "Pre-Work": [
            ("Generate concepts", lambda r: r.key_metrics.get("concepts_generated", 0) > 0 or "QUOTA EXHAUSTED" in str(r.run.log_content)),
            ("Save artifact", lambda r: r.persistent_write_success),
        ],
        "Analytics Feedback": [
            ("Fetch YouTube data", lambda r: r.key_metrics.get("videos_analyzed", 0) > 0 or r.key_metrics.get("skipped_by_ai")),
            ("AI analysis", lambda r: bool(r.key_metrics.get("ai_insight")) or r.key_metrics.get("skipped_by_ai")),
            ("Update patterns", lambda r: r.key_metrics.get("pattern_files_updated", 0) > 0 or r.key_metrics.get("skipped_by_ai")),
        ],
        "Monthly": [
            ("Run analysis", lambda r: r.expected_behavior_met),
            ("Save patterns", lambda r: r.persistent_write_success),
        ]
    }
    
    for wf_key, checks in behavior_checks.items():
        matching_results = [r for r in results if wf_key in r.run.name]
        if not matching_results:
            continue
        
        safe_print(f"\n   📊 {wf_key}")
        for check_name, check_fn in checks:
            passed = sum(1 for r in matching_results if check_fn(r))
            total = len(matching_results)
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            safe_print(f"      {status} {check_name}: {passed}/{total}")
    
    # ============================================================
    # SECTION 4: Persistent Data Read/Write
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  4. PERSISTENT DATA HEALTH")
    safe_print("-" * 80)
    
    read_success = sum(1 for r in results if r.persistent_read_success)
    write_success = sum(1 for r in results if r.persistent_write_success)
    
    safe_print(f"\n   📖 Persistent Read Success:  {read_success}/{len(results)} ({read_success/len(results)*100:.0f}%)")
    safe_print(f"   📝 Persistent Write Success: {write_success}/{len(results)} ({write_success/len(results)*100:.0f}%)")
    
    # ============================================================
    # SECTION 5: Detailed Quota Usage Report (Per Model)
    # ============================================================
    safe_print("\n" + "-" * 90)
    safe_print("  5. QUOTA USAGE REPORT (Per Model with % of Daily Limit)")
    safe_print("-" * 90)
    
    # Aggregate quota by provider and model
    quota_details: Dict[str, Dict[str, Dict]] = {}  # provider -> model -> {calls, limit, percent}
    rate_limited = []
    
    # Special tracking for YouTube per-day limits
    youtube_per_day: Dict[str, int] = {}  # date -> upload count
    
    for r in results:
        for q in r.quota_usage:
            if q.provider not in quota_details:
                quota_details[q.provider] = {}
            
            endpoint_key = q.endpoint or q.model or "unknown"
            if endpoint_key not in quota_details[q.provider]:
                quota_details[q.provider][endpoint_key] = {
                    "calls": 0, 
                    "limit": q.daily_limit,
                    "workflows": set(),
                    "per_day": {}  # Track per-day for daily-limited quotas
                }
            
            quota_details[q.provider][endpoint_key]["calls"] += q.calls
            quota_details[q.provider][endpoint_key]["workflows"].add(r.run.name[:20])
            
            # Track per-day for YouTube uploads
            if q.provider == "YOUTUBE" and "upload" in endpoint_key.lower():
                day_key = r.run.created_at.strftime("%Y-%m-%d")
                if "per_day" not in quota_details[q.provider][endpoint_key]:
                    quota_details[q.provider][endpoint_key]["per_day"] = {}
                quota_details[q.provider][endpoint_key]["per_day"][day_key] = \
                    quota_details[q.provider][endpoint_key]["per_day"].get(day_key, 0) + q.calls
            
            if q.error_429:
                rate_limited.append((q.provider, endpoint_key, r.run.run_id, r.run.created_at))
    
    safe_print(f"\n   {'Provider':<12} | {'Model/Endpoint':<30} | {'Calls':>6} | {'Limit':>8} | {'% Used':>8} | {'Status':<10}")
    safe_print("   " + "-" * 95)
    
    total_calls = 0
    for provider in sorted(quota_details.keys()):
        for endpoint, data in sorted(quota_details[provider].items()):
            calls = data["calls"]
            limit = data["limit"]
            total_calls += calls
            
            # For YouTube uploads, check per-day usage (limit is per DAY, not total)
            if provider == "YOUTUBE" and "upload" in endpoint.lower() and data.get("per_day"):
                max_day_usage = max(data["per_day"].values()) if data["per_day"] else 0
                percent = max_day_usage / limit * 100 if limit > 0 else 0
                percent_str = f"{percent:.1f}%/day"
                status = "⚠️ HIGH" if percent >= 80 else "✅ OK"
                # Show per-day breakdown
                days_info = ", ".join([f"{d[-5:]}: {c}" for d, c in sorted(data["per_day"].items())[-3:]])
                safe_print(f"   {provider:<12} | {endpoint[:30]:<30} | {calls:>6} | {limit:>5}/day | {percent_str:>8} | {status:<10}")
                safe_print(f"   {'':12} | {'  └─ Per day: ' + days_info:<62}")
            elif limit > 0:
                percent = calls / limit * 100
                percent_str = f"{percent:.1f}%"
                if percent >= 80:
                    status = "⚠️ HIGH"
                elif percent >= 50:
                    status = "📊 MEDIUM"
                else:
                    status = "✅ OK"
                limit_str = str(limit)
                safe_print(f"   {provider:<12} | {endpoint[:30]:<30} | {calls:>6} | {limit_str:>8} | {percent_str:>8} | {status:<10}")
            else:
                percent_str = "∞ FREE"
                status = "✅ FREE"
                safe_print(f"   {provider:<12} | {endpoint[:30]:<30} | {calls:>6} | {'∞':>8} | {percent_str:>8} | {status:<10}")
    
    safe_print("   " + "-" * 95)
    safe_print(f"   {'TOTAL':<12} | {'':<30} | {total_calls:>6} |")
    
    if rate_limited:
        safe_print("\n   ⚠️ RATE LIMIT / 429 EVENTS DETECTED:")
        for provider, endpoint, run_id, dt in rate_limited[:10]:
            safe_print(f"      - {provider}/{endpoint} @ Run #{run_id} ({dt.strftime('%Y-%m-%d %H:%M')})")
    else:
        safe_print("\n   ✅ No rate limit (429) events detected")
    
    # ============================================================
    # SECTION 6: Video Characteristics & Scores Table
    # ============================================================
    all_videos = []
    for r in results:
        for v in r.videos:
            v.run_id = r.run.run_id
            v.run_time = r.run.created_at
            all_videos.append(v)
    
    if all_videos:
        safe_print("\n" + "-" * 90)
        safe_print("  6. VIDEO GENERATION REPORT (Characteristics & Scores)")
        safe_print("-" * 90)
        
        safe_print(f"\n   Total Videos Generated: {len(all_videos)}")
        uploaded = sum(1 for v in all_videos if v.uploaded)
        safe_print(f"   Successfully Uploaded:  {uploaded}")
        avg_size = sum(v.file_size_mb for v in all_videos if v.file_size_mb) / len(all_videos) if all_videos else 0
        safe_print(f"   Average File Size:      {avg_size:.1f}MB")
        
        # Summary table
        safe_print(f"\n   {'#':<3} | {'Date':<12} | {'Category':<15} | {'Size':>6} | {'Upload':>7} | {'YouTube URL':<30}")
        safe_print("   " + "-" * 95)
        
        for i, v in enumerate(sorted(all_videos, key=lambda x: getattr(x, 'run_time', datetime.min), reverse=True), 1):
            time_str = getattr(v, 'run_time', datetime.min).strftime("%Y-%m-%d") if hasattr(v, 'run_time') else "N/A"
            status = "✅" if v.uploaded else "❌"
            category = v.category[:15] if v.category else "Unknown"
            size = f"{v.file_size_mb}MB" if v.file_size_mb else "?"
            yt_url = v.youtube_url[:30] if v.youtube_url else "N/A"
            safe_print(f"   {i:<3} | {time_str:<12} | {category:<15} | {size:>6} | {status:>7} | {yt_url:<30}")
        
        # Detailed characteristics per video
        safe_print(f"\n   VIDEO CHARACTERISTICS DETAIL:")
        safe_print("   " + "-" * 90)
        
        for i, v in enumerate(sorted(all_videos, key=lambda x: getattr(x, 'run_time', datetime.min), reverse=True), 1):
            safe_print(f"\n   📹 Video #{i}: {v.title}")
            safe_print(f"      Category: {v.category or 'N/A'} | Size: {v.file_size_mb}MB | Duration: {v.duration or 'N/A'}s")
            
            # Scores
            scores = []
            if v.virality_score: scores.append(f"Virality: {v.virality_score}")
            if v.engagement_score: scores.append(f"Engagement: {v.engagement_score}")
            if v.retention_score: scores.append(f"Retention: {v.retention_score}")
            if v.script_score: scores.append(f"Script: {v.script_score}")
            if scores:
                safe_print(f"      Scores: {' | '.join(scores)}")
            
            # Quality gate
            if v.quality_gate_passed:
                safe_print(f"      Quality Gate: ✅ PASSED")
            elif v.quality_gate_reason:
                safe_print(f"      Quality Gate: ❌ FAILED - {v.quality_gate_reason}")
            
            # Technical details
            tech = []
            if v.ai_model_used: tech.append(f"AI: {v.ai_model_used}")
            if v.tts_engine: tech.append(f"TTS: {v.tts_engine}")
            if v.phrase_count: tech.append(f"Phrases: {v.phrase_count}")
            if v.b_roll_count: tech.append(f"B-roll: {v.b_roll_count}")
            if tech:
                safe_print(f"      Technical: {' | '.join(tech)}")
            
            # Hook
            if v.hook:
                safe_print(f"      Hook: \"{v.hook}\"")
            
            # Upload status
            if v.uploaded:
                safe_print(f"      Platform: {v.platform} | URL: {v.youtube_url or v.video_id or 'N/A'}")
    
    # ============================================================
    # SECTION 7: Errors and Warnings Summary
    # ============================================================
    all_errors = []
    all_warnings = []
    for r in results:
        for e in r.errors:
            all_errors.append((r.run.name, r.run.run_id, e))
        for w in r.warnings:
            all_warnings.append((r.run.name, r.run.run_id, w))
    
    if all_errors or all_warnings:
        safe_print("\n" + "-" * 80)
        safe_print("  7. ERRORS & WARNINGS")
        safe_print("-" * 80)
        
        if all_errors:
            safe_print("\n   ❌ ERRORS:")
            for wf, run_id, err in all_errors[:10]:
                safe_print(f"      [{wf[:20]}] Run #{run_id}: {err[:50]}")
        
        if all_warnings:
            safe_print("\n   ⚠️ WARNINGS:")
            for wf, run_id, warn in all_warnings[:10]:
                safe_print(f"      [{wf[:20]}] Run #{run_id}: {warn[:50]}")
    
    # ============================================================
    # SECTION 8: HIDDEN ISSUES DETECTION
    # ============================================================
    safe_print("\n" + "-" * 90)
    safe_print("  8. HIDDEN ISSUES DETECTION")
    safe_print("-" * 90)
    
    hidden_issues = []
    
    # Issue 1: Persistent data not being read/written correctly
    for r in results:
        if "Video Generator" in r.run.name:
            if r.passed and not r.persistent_read_success:
                hidden_issues.append(f"Run #{r.run.run_id}: Video generated but persistent data not read")
            if r.passed and not r.persistent_write_success:
                hidden_issues.append(f"Run #{r.run.run_id}: Video generated but persistent data not saved")
    
    # Issue 2: Pre-work not being used
    generator_results = [r for r in results if "Video Generator" in r.run.name]
    for r in generator_results:
        if r.passed and r.key_metrics.get("prework_concepts_used", 0) == 0:
            hidden_issues.append(f"Run #{r.run.run_id}: Pre-work concepts not used (quota wasted on fresh generation)")
    
    # Issue 3: Videos generated but not uploaded (when upload was expected)
    for r in generator_results:
        if r.passed and r.videos:
            not_uploaded = [v for v in r.videos if not v.uploaded]
            if not_uploaded and "no-upload" not in str(r.run.log_content).lower():
                hidden_issues.append(f"Run #{r.run.run_id}: {len(not_uploaded)} video(s) generated but not uploaded")
    
    # Issue 4: Stale persistent data
    if persistent_data:
        for fname, analysis in persistent_data.items():
            if analysis.health_status == "stale":
                hidden_issues.append(f"Stale file: {fname} - not updated for >7 days")
            if analysis.health_status == "empty":
                hidden_issues.append(f"Empty file: {fname} - no meaningful data")
            if analysis.health_status == "corrupted":
                hidden_issues.append(f"Corrupted file: {fname} - JSON parse error")
    
    # Issue 5: High rate limit frequency
    if len(rate_limited) > 3:
        hidden_issues.append(f"Frequent rate limits: {len(rate_limited)} events - consider reducing API call frequency")
    
    # Issue 6: Low video generation success rate
    if generator_results:
        gen_passed = sum(1 for r in generator_results if r.passed and r.videos)
        gen_total = len(generator_results)
        if gen_total > 0 and gen_passed / gen_total < 0.8:
            hidden_issues.append(f"Low video success rate: {gen_passed}/{gen_total} ({gen_passed/gen_total*100:.0f}%)")
    
    # Issue 7: Missing expected workflow runs
    expected_workflows = {
        "Video Generator": 6,  # Expected per day
        "Pre-Work": 1,  # Expected per day
    }
    for wf_name, expected_per_day in expected_workflows.items():
        matching = [r for r in results if wf_name in r.run.name]
        expected_in_period = expected_per_day * days
        if len(matching) < expected_in_period * 0.5:  # Less than 50% of expected
            hidden_issues.append(f"Missing {wf_name} runs: Expected ~{expected_in_period}, got {len(matching)}")
    
    # Issue 8: Consistent "fresh state" warnings (means persistent data not persisting)
    fresh_state_count = sum(1 for r in results for w in r.warnings if "Fresh state" in w)
    if fresh_state_count > len(generator_results) * 0.5:
        hidden_issues.append(f"Persistent state issues: {fresh_state_count}/{len(generator_results)} runs started fresh")
    
    if hidden_issues:
        safe_print("\n   🔍 DETECTED HIDDEN ISSUES:")
        for i, issue in enumerate(hidden_issues, 1):
            safe_print(f"      {i}. ⚠️ {issue}")
    else:
        safe_print("\n   ✅ No hidden issues detected!")
    
    # ============================================================
    # SECTION 9: Additional Metrics
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  9. ADDITIONAL METRICS")
    safe_print("-" * 80)
    
    # Pre-work effectiveness
    prework_results = [r for r in results if "Pre-Work" in r.run.name]
    if prework_results:
        total_concepts = sum(r.key_metrics.get("concepts_generated", 0) for r in prework_results)
        safe_print(f"\n   📦 Pre-Work Concepts Generated: {total_concepts}")
    
    # Analytics insights
    analytics_results = [r for r in results if "Analytics" in r.run.name or "Weekly" in r.run.name]
    if analytics_results:
        insights = [r.key_metrics.get("ai_insight") for r in analytics_results if r.key_metrics.get("ai_insight")]
        if insights:
            safe_print(f"\n   🧠 Latest AI Insight:")
            safe_print(f"      \"{insights[0][:100]}...\"")
    
    # Video generator health
    generator_results = [r for r in results if "Video Generator" in r.run.name]
    if generator_results:
        avg_videos = sum(len(r.videos) for r in generator_results) / len(generator_results) if generator_results else 0
        safe_print(f"\n   🎬 Avg Videos per Run: {avg_videos:.1f}")
    
    # ============================================================
    # SECTION 10: Persistent Data Analysis
    # ============================================================
    if persistent_data:
        safe_print("\n" + "-" * 90)
        safe_print("  10. PERSISTENT DATA ANALYSIS")
        safe_print("-" * 90)
        
        safe_print(f"\n   {'File':<30} | {'Status':<12} | {'Size':>8} | {'Key Info':<35}")
        safe_print("   " + "-" * 95)
        
        for fname, analysis in persistent_data.items():
            status_icon = {
                "healthy": "✅",
                "stale": "⚠️",
                "empty": "📭",
                "missing": "❌",
                "corrupted": "💥"
            }.get(analysis.health_status, "❓")
            
            status = f"{status_icon} {analysis.health_status}"
            size = f"{analysis.size_bytes//1024}KB" if analysis.size_bytes else "0"
            
            # Format key info
            key_info = ""
            if analysis.key_fields:
                key_items = []
                for k, v in list(analysis.key_fields.items())[:2]:
                    if isinstance(v, list):
                        key_items.append(f"{k}: {len(v)} items")
                    elif isinstance(v, str) and len(v) > 20:
                        key_items.append(f"{k}: {v[:17]}...")
                    else:
                        key_items.append(f"{k}: {v}")
                key_info = ", ".join(key_items)[:35]
            
            safe_print(f"   {fname:<30} | {status:<12} | {size:>8} | {key_info:<35}")
        
        # Detailed analysis for key files
        safe_print("\n   DETAILED PERSISTENT DATA:")
        
        for fname, analysis in persistent_data.items():
            if analysis.exists and analysis.key_fields:
                safe_print(f"\n   📄 {fname}:")
                for key, value in analysis.key_fields.items():
                    if isinstance(value, list):
                        safe_print(f"      {key}: {value[:3]}{'...' if len(value) > 3 else ''}")
                    else:
                        safe_print(f"      {key}: {value}")
    
    # ============================================================
    # SECTION 11: Per-Workflow Quota Breakdown
    # ============================================================
    safe_print("\n" + "-" * 90)
    safe_print("  11. PER-WORKFLOW QUOTA BREAKDOWN")
    safe_print("-" * 90)
    
    for r in sorted(results, key=lambda x: x.run.created_at, reverse=True)[:10]:
        if r.quota_usage:
            safe_print(f"\n   📊 {r.run.name[:40]} (Run #{r.run.run_id})")
            safe_print(f"      Time: {r.run.created_at.strftime('%Y-%m-%d %H:%M')} | Status: {'✅' if r.passed else '❌'}")
            
            for q in r.quota_usage:
                limit_str = str(q.daily_limit) if q.daily_limit > 0 else "∞"
                percent_str = f"{q.percent_used:.1f}%" if q.daily_limit > 0 else "FREE"
                status = "⚠️ 429!" if q.error_429 else ""
                safe_print(f"      - {q.provider}/{q.endpoint}: {q.calls} calls ({percent_str} of {limit_str}/day) {status}")
    
    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    safe_print("\n" + "=" * 90)
    safe_print("  FINAL SUMMARY")
    safe_print("=" * 90)
    
    overall_health = "🟢 HEALTHY" if total_passed == total_runs else "🟡 DEGRADED" if total_passed > total_runs * 0.8 else "🔴 UNHEALTHY"
    
    safe_print(f"\n   System Health: {overall_health}")
    safe_print(f"   Success Rate:  {total_passed}/{total_runs} ({overall_rate})")
    safe_print(f"   Videos Generated: {len(all_videos)}")
    safe_print(f"   Videos Uploaded:  {uploaded}")
    safe_print(f"   Rate Limits: {'⚠️ ' + str(len(rate_limited)) + ' events' if rate_limited else '✅ None'}")
    
    # Quota summary
    if quota_details:
        safe_print("\n   Quota Status by Provider:")
        for provider in sorted(quota_details.keys()):
            total_provider_calls = sum(d["calls"] for d in quota_details[provider].values())
            total_provider_limit = sum(d["limit"] for d in quota_details[provider].values() if d["limit"] > 0)
            if total_provider_limit > 0:
                pct = total_provider_calls / total_provider_limit * 100
                safe_print(f"      {provider}: {total_provider_calls} calls (~{pct:.1f}% of daily limits)")
            else:
                safe_print(f"      {provider}: {total_provider_calls} calls (FREE endpoints)")
    
    # Persistent data summary
    if persistent_data:
        healthy_count = sum(1 for a in persistent_data.values() if a.health_status == "healthy")
        total_files = len(persistent_data)
        safe_print(f"\n   Persistent Data: {healthy_count}/{total_files} files healthy")
    
    safe_print("\n" + "=" * 90)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze scheduled workflow runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analyze_workflows.py --days 1    # Last 24 hours
  python scripts/analyze_workflows.py --days 2    # Last 48 hours
  python scripts/analyze_workflows.py --days 7    # Last week
        """
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=1,
        help="Number of days to analyze (default: 1)"
    )
    
    args = parser.parse_args()
    
    safe_print("=" * 80)
    safe_print("  WORKFLOW ANALYZER")
    safe_print(f"  Analyzing last {args.days} day(s) of scheduled workflows")
    safe_print("=" * 80)
    
    # Step 1: Get scheduled runs
    runs = get_scheduled_runs(args.days)
    
    if not runs:
        safe_print("\n[INFO] No scheduled workflow runs found in the specified period.")
        return
    
    # Step 2: Analyze each run
    safe_print(f"\n[2/6] Analyzing {len(runs)} workflow runs...")
    results = []
    
    for i, run in enumerate(runs, 1):
        safe_print(f"\n   [{i}/{len(runs)}] Analyzing: {run.name}")
        safe_print(f"      Run ID: {run.run_id} | Status: {run.conclusion}")
        
        result = analyze_workflow_run(run)
        results.append(result)
    
    # Step 3: Download and analyze persistent data
    safe_print(f"\n[3/6] Downloading persistent data...")
    persistent_data = download_persistent_data()
    
    # Step 4-6: Generate report
    safe_print(f"\n[4/6] Generating comprehensive report...")
    generate_report(results, args.days, persistent_data)
    
    safe_print("\n✅ Comprehensive analysis complete!")


if __name__ == "__main__":
    main()


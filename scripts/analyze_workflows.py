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
    duration: float = 0
    phrase_count: int = 0
    hook: str = ""
    music_mood: str = ""
    virality_score: float = 0
    engagement_score: float = 0
    retention_score: float = 0
    quality_gate_passed: bool = False
    uploaded: bool = False
    platform: str = ""
    video_id: str = ""
    file_size_mb: float = 0

@dataclass
class QuotaUsage:
    """Quota usage for a workflow."""
    provider: str
    endpoint: str
    calls: int
    model: str = ""
    limit_reached: bool = False
    error_429: bool = False

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
# WORKFLOW ANALYZERS (One per workflow type)
# ============================================================

def analyze_video_generator(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    """Analyze ViralShorts Factory - Auto Video Generator run."""
    result = WorkflowAnalysisResult(run=run)
    
    # Check if passed
    result.passed = run.conclusion == "success"
    
    # Check persistent data read
    if "Restored patterns from artifact" in log or "[OK] Restored" in log:
        result.persistent_read_success = True
    if "No previous state found" in log:
        result.persistent_read_success = True  # Valid - fresh start
        result.warnings.append("Fresh state (no previous persistent data)")
    
    # Check persistent data write
    if "persistent-state" in log and "Artifact name is valid" in log:
        result.persistent_write_success = True
    
    # Check pre-generated concepts loaded
    if "Loaded" in log and "pre-generated concepts" in log:
        match = re.search(r'Loaded (\d+) pre-generated concepts', log)
        if match:
            result.key_metrics["prework_concepts_used"] = int(match.group(1))
    
    # Extract video information
    videos = []
    
    # Pattern: Generated video info
    video_patterns = [
        # Duration and size
        r'output/([^.]+\.mp4)\s*\((\d+)MB\)',
        r'Generated \d+ video',
        # Video characteristics from log
        r'Topic:\s*([^\n]+)',
        r'Hook:\s*([^\n]+)',
        r'Virality Score:\s*([\d.]+)',
        r'Quality Gate:\s*(PASSED|FAILED)',
    ]
    
    # Find video file mentions - use unique set to avoid duplicates
    video_files = set(re.findall(r'output/(pro_[^\s]+\.mp4)', log))  # Only pro_*.mp4 files
    for vf in video_files:
        video = VideoInfo(title=vf)
        
        # Try to get size
        size_match = re.search(rf'{re.escape(vf)}\s*\((\d+)MB\)', log)
        if size_match:
            video.file_size_mb = float(size_match.group(1))
        
        videos.append(video)
    
    # Check for uploaded - look for various upload patterns
    upload_patterns = [
        "Successfully uploaded to YouTube",
        "Upload complete",
        "[YOUTUBE] Uploading:",
        "[UPLOAD] Title:"
    ]
    if any(pattern in log for pattern in upload_patterns):
        for v in videos:
            v.uploaded = True
            v.platform = "YouTube"
    
    # Extract YouTube video IDs
    yt_ids = re.findall(r'youtube\.com/shorts/([a-zA-Z0-9_-]+)', log)
    for i, vid in enumerate(yt_ids):
        if i < len(videos):
            videos[i].video_id = vid
    
    result.videos = videos
    
    # Check expected behavior
    if result.passed and len(videos) > 0:
        if videos[0].uploaded or "no-upload" in log.lower() or "test mode" in log.lower():
            result.expected_behavior_met = True
    
    # Extract quota usage
    result.quota_usage = extract_quota_usage(log)
    
    # Check for errors - but exclude false positives from echo statements
    # Only report "No videos were generated" if no videos were actually found
    if "CRITICAL" in log and "No videos were generated" in log and len(videos) == 0:
        result.errors.append("No videos were generated")
    elif "CRITICAL" in log:
        errors = re.findall(r'CRITICAL[:\s]+([^\n\[]+)', log)
        # Filter out ANSI codes, duplicates, and the "No videos" message if videos exist
        clean_errors = list(set(
            e.strip() for e in errors 
            if e.strip() 
            and not e.startswith('[0m')
            and not (len(videos) > 0 and "No videos" in e)
        ))
        result.errors.extend(clean_errors[:5])
    
    # Rate limit handling is done in extract_quota_usage() - no need for UNKNOWN entry
    
    # Extract scores if present
    virality_match = re.search(r'virality[_\s]?score[:\s]*([\d.]+)', log, re.IGNORECASE)
    if virality_match:
        result.key_metrics["virality_score"] = float(virality_match.group(1))
    
    engagement_match = re.search(r'engagement[_\s]?score[:\s]*([\d.]+)', log, re.IGNORECASE)
    if engagement_match:
        result.key_metrics["engagement_score"] = float(engagement_match.group(1))
    
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
    result.quota_usage = extract_quota_usage(log)
    
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
    result.quota_usage = extract_quota_usage(log)
    
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
    result.quota_usage = extract_quota_usage(log)
    
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


def generate_report(results: List[WorkflowAnalysisResult], days: int):
    """Generate comprehensive analysis report."""
    
    safe_print("\n" + "=" * 80)
    safe_print("  WORKFLOW ANALYSIS REPORT")
    safe_print(f"  Period: Last {days} day(s)")
    safe_print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    safe_print("=" * 80)
    
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
    # SECTION 5: Quota Usage Report
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  5. QUOTA USAGE REPORT")
    safe_print("-" * 80)
    
    # Aggregate quota by provider
    quota_by_provider: Dict[str, Dict[str, int]] = {}
    rate_limited = []
    
    for r in results:
        for q in r.quota_usage:
            if q.provider not in quota_by_provider:
                quota_by_provider[q.provider] = {"calls": 0, "workflows": set()}
            quota_by_provider[q.provider]["calls"] += q.calls
            quota_by_provider[q.provider]["workflows"].add(r.run.name)
            
            if q.error_429:
                rate_limited.append((q.provider, r.run.run_id, r.run.created_at))
    
    safe_print(f"\n   {'Provider':<15} | {'Total Calls':>12} | {'Used By':<40}")
    safe_print("   " + "-" * 75)
    
    for provider, data in sorted(quota_by_provider.items()):
        wfs = ", ".join(list(data["workflows"])[:2])
        if len(data["workflows"]) > 2:
            wfs += f" +{len(data['workflows'])-2}"
        safe_print(f"   {provider:<15} | {data['calls']:>12} | {wfs:<40}")
    
    if rate_limited:
        safe_print("\n   ⚠️ RATE LIMIT EVENTS:")
        for provider, run_id, dt in rate_limited[:5]:
            safe_print(f"      - {provider} @ Run #{run_id} ({dt.strftime('%Y-%m-%d %H:%M')})")
    else:
        safe_print("\n   ✅ No rate limit events detected")
    
    # ============================================================
    # SECTION 6: Video Characteristics Table
    # ============================================================
    all_videos = []
    for r in results:
        for v in r.videos:
            v.run_id = r.run.run_id
            v.run_time = r.run.created_at
            all_videos.append(v)
    
    if all_videos:
        safe_print("\n" + "-" * 80)
        safe_print("  6. VIDEO GENERATION REPORT")
        safe_print("-" * 80)
        
        safe_print(f"\n   Total Videos Generated: {len(all_videos)}")
        uploaded = sum(1 for v in all_videos if v.uploaded)
        safe_print(f"   Successfully Uploaded:  {uploaded}")
        
        safe_print(f"\n   {'Date/Time':<18} | {'Title':<35} | {'Size':>6} | {'Status':<10}")
        safe_print("   " + "-" * 80)
        
        for v in sorted(all_videos, key=lambda x: getattr(x, 'run_time', datetime.min), reverse=True):
            time_str = getattr(v, 'run_time', datetime.min).strftime("%Y-%m-%d %H:%M") if hasattr(v, 'run_time') else "N/A"
            status = "✅ Uploaded" if v.uploaded else "📁 Local"
            title = v.title[:33] if v.title else "Unknown"
            size = f"{v.file_size_mb}MB" if v.file_size_mb else "?"
            safe_print(f"   {time_str:<18} | {title:<35} | {size:>6} | {status:<10}")
    
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
    # SECTION 8: Additional Metrics
    # ============================================================
    safe_print("\n" + "-" * 80)
    safe_print("  8. ADDITIONAL METRICS")
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
    # FINAL SUMMARY
    # ============================================================
    safe_print("\n" + "=" * 80)
    safe_print("  FINAL SUMMARY")
    safe_print("=" * 80)
    
    overall_health = "🟢 HEALTHY" if total_passed == total_runs else "🟡 DEGRADED" if total_passed > total_runs * 0.8 else "🔴 UNHEALTHY"
    
    safe_print(f"\n   System Health: {overall_health}")
    safe_print(f"   Success Rate:  {total_passed}/{total_runs} ({overall_rate})")
    safe_print(f"   Videos Generated: {len(all_videos)}")
    safe_print(f"   Rate Limits: {'⚠️ ' + str(len(rate_limited)) + ' events' if rate_limited else '✅ None'}")
    
    safe_print("\n" + "=" * 80)


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
    
    # Step 3-6: Generate report
    safe_print(f"\n[3/6] Generating report...")
    generate_report(results, args.days)
    
    safe_print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()


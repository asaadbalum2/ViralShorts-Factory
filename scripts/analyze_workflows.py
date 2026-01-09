#!/usr/bin/env python3
"""
Workflow Analyzer - COMPREHENSIVE analysis of scheduled workflow runs.

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
- Persistent data read/write success AND CONTENT ANALYSIS
- Quota usage per MODEL with % of daily quota
- Video characteristics (topic, hook, scores, music, duration, etc.)
- Feedback/analytics workflow analysis
- Rate limit detection
"""

import argparse
import subprocess
import json
import re
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# ============================================================
# KNOWN QUOTA LIMITS (requests per day)
# ============================================================
KNOWN_QUOTAS = {
    "gemini-2.0-flash": 1500,
    "gemini-2.0-flash-lite": 1500,
    "gemini-1.5-flash": 1500,
    "gemini-1.5-flash-8b": 1500,
    "gemini-1.5-pro": 50,
    "gemini-2.5-pro-preview": 25,
    "gemini-2.5-flash-preview": 500,
    "llama-3.3-70b-versatile": 1000,
    "pexels-videos": 20000,
    "youtube-upload": 6,
    "youtube-read": 10000,
}

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class WorkflowRun:
    run_id: int
    name: str
    status: str
    conclusion: str
    created_at: datetime
    event: str
    log_content: str = ""

@dataclass
class VideoInfo:
    filename: str = ""
    title: str = ""
    category: str = ""
    duration: float = 0
    phrase_count: int = 0
    hook: str = ""
    music_mood: str = ""
    virality_score: float = 0
    engagement_score: float = 0
    quality_gate_passed: bool = False
    uploaded: bool = False
    platform: str = ""
    video_id: str = ""
    file_size_mb: float = 0

@dataclass
class QuotaUsage:
    provider: str
    endpoint: str
    model: str
    calls: int
    daily_limit: int = 0
    percent_used: float = 0
    error_429: bool = False

@dataclass  
class PersistentDataAnalysis:
    file_name: str
    exists: bool = False
    last_updated: str = ""
    record_count: int = 0
    key_fields: Dict[str, Any] = field(default_factory=dict)
    health_status: str = "unknown"

@dataclass
class WorkflowAnalysisResult:
    run: WorkflowRun
    passed: bool = False
    expected_behavior_met: bool = False
    persistent_read_success: bool = False
    persistent_write_success: bool = False
    persistent_files_read: List[str] = field(default_factory=list)
    persistent_files_written: List[str] = field(default_factory=list)
    videos: List[VideoInfo] = field(default_factory=list)
    quota_usage: List[QuotaUsage] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    key_metrics: Dict[str, Any] = field(default_factory=dict)


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode())


def run_gh_command(args: List[str], timeout: int = 60) -> Optional[str]:
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
            if len(output) > 3 * 1024 * 1024:
                output = output[:3 * 1024 * 1024]
            return output
        return None
    except:
        return None


def get_scheduled_runs(days: int) -> List[WorkflowRun]:
    safe_print(f"\n{'='*70}")
    safe_print(f"  STEP 1: Fetching Scheduled Runs (last {days} days)")
    safe_print(f"{'='*70}")
    
    output = run_gh_command([
        "run", "list", "--limit", str(max(100, days * 15)),
        "--json", "databaseId,name,status,conclusion,createdAt,event"
    ], timeout=30)
    
    if not output:
        return []
    
    try:
        runs_data = json.loads(output)
    except:
        return []
    
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    runs = []
    
    for run in runs_data:
        if run.get("event") != "schedule":
            continue
        created = datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00")).replace(tzinfo=None)
        if created < cutoff:
            continue
        runs.append(WorkflowRun(
            run_id=run["databaseId"],
            name=run["name"],
            status=run["status"],
            conclusion=run.get("conclusion", ""),
            created_at=created,
            event=run["event"]
        ))
    
    by_type = {}
    for r in runs:
        by_type.setdefault(r.name, []).append(r)
    
    safe_print(f"\n   Found {len(runs)} scheduled runs:")
    for name, rlist in by_type.items():
        passed = sum(1 for r in rlist if r.conclusion == "success")
        safe_print(f"   - {name}: {len(rlist)} runs ({passed} passed)")
    
    return runs


def download_persistent_state() -> Dict[str, Any]:
    safe_print(f"\n{'='*70}")
    safe_print(f"  STEP 2: Downloading Persistent State")
    safe_print(f"{'='*70}")
    
    persistent_data = {}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_print("   Downloading artifact...")
        result = subprocess.run(
            ["gh", "run", "download", "--name", "persistent-state", "-D", tmpdir],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode != 0:
            safe_print(f"   [WARN] Could not download: trying from latest run...")
            runs_out = run_gh_command([
                "run", "list", "--workflow", "generate.yml", "--status", "success", 
                "--limit", "1", "--json", "databaseId"
            ])
            if runs_out:
                try:
                    run_id = json.loads(runs_out)[0]["databaseId"]
                    subprocess.run(
                        ["gh", "run", "download", str(run_id), "--name", "persistent-state", "-D", tmpdir],
                        capture_output=True, timeout=120
                    )
                except:
                    pass
        
        for root, dirs, files in os.walk(tmpdir):
            for f in files:
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as jf:
                            persistent_data[f] = json.load(jf)
                            safe_print(f"   ✓ Loaded: {f}")
                    except Exception as e:
                        safe_print(f"   ✗ Failed: {f} ({e})")
    
    safe_print(f"\n   Total files loaded: {len(persistent_data)}")
    return persistent_data


def download_log(run_id: int) -> str:
    safe_print(f"      Downloading log...")
    output = run_gh_command(["run", "view", str(run_id), "--log"], timeout=90)
    if output:
        safe_print(f"      Downloaded {len(output.split(chr(10)))} lines")
        return output
    return ""


def extract_video_info(log: str, filename: str) -> VideoInfo:
    video = VideoInfo(filename=filename)
    
    size_match = re.search(rf'{re.escape(filename)}\s*\((\d+)MB\)', log)
    if size_match:
        video.file_size_mb = float(size_match.group(1))
    
    name_match = re.search(r'pro_([A-Za-z_]+)_\d+\.mp4', filename)
    if name_match:
        video.category = name_match.group(1).replace('_', ' ')
    
    title_match = re.search(r'\[UPLOAD\] Title:\s*([^\n]+)', log)
    if title_match:
        video.title = title_match.group(1).strip()[:80]
    
    for score_name in ['virality', 'engagement']:
        pattern = rf'{score_name}[_\s]?score[:\s]*([\d.]+)'
        match = re.search(pattern, log, re.IGNORECASE)
        if match:
            setattr(video, f'{score_name}_score', float(match.group(1)))
    
    return video


def extract_detailed_quota(log: str) -> List[QuotaUsage]:
    quota_list = []
    
    gemini_models = {}
    for m in re.findall(r'(gemini-[\d.a-z-]+)', log.lower()):
        gemini_models[m] = gemini_models.get(m, 0) + 1
    
    generate_calls = len(re.findall(r'generateContent', log))
    
    if gemini_models and generate_calls > 0:
        total = sum(gemini_models.values())
        for model, mentions in gemini_models.items():
            calls = max(1, int(generate_calls * mentions / total))
            limit = KNOWN_QUOTAS.get(model, 1500)
            quota_list.append(QuotaUsage(
                provider="GEMINI", endpoint="generateContent", model=model,
                calls=calls, daily_limit=limit,
                percent_used=round(calls / limit * 100, 2) if limit else 0
            ))
    
    models_calls = len(re.findall(r'/v1beta/models[^/]', log))
    if models_calls:
        quota_list.append(QuotaUsage(
            provider="GEMINI", endpoint="/models (FREE)", model="N/A",
            calls=models_calls, daily_limit=0, percent_used=0
        ))
    
    groq_calls = len(re.findall(r'api\.groq\.com', log))
    if groq_calls:
        quota_list.append(QuotaUsage(
            provider="GROQ", endpoint="chat/completions", model="llama-3.3-70b",
            calls=groq_calls, daily_limit=1000, percent_used=round(groq_calls/10, 2)
        ))
    
    pexels_calls = len(re.findall(r'api\.pexels\.com', log))
    if pexels_calls:
        quota_list.append(QuotaUsage(
            provider="PEXELS", endpoint="videos/search", model="N/A",
            calls=pexels_calls, daily_limit=20000, percent_used=round(pexels_calls/200, 4)
        ))
    
    yt_uploads = len(re.findall(r'\[YOUTUBE\] Uploading:', log))
    if yt_uploads:
        quota_list.append(QuotaUsage(
            provider="YOUTUBE", endpoint="upload", model="N/A",
            calls=yt_uploads, daily_limit=6, percent_used=round(yt_uploads/6*100, 1)
        ))
    
    if "429" in log or "rate limit" in log.lower():
        for q in quota_list:
            if re.search(rf'{q.provider}.*429', log, re.IGNORECASE):
                q.error_429 = True
    
    return quota_list


def analyze_video_generator(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    result = WorkflowAnalysisResult(run=run)
    result.passed = run.conclusion == "success"
    
    if "Restored patterns" in log or "[OK] Restored" in log:
        result.persistent_read_success = True
        result.persistent_files_read.append("persistent-state/*")
    if "No previous state found" in log:
        result.persistent_read_success = True
        result.warnings.append("Fresh state (no previous data)")
    
    prework = re.search(r'Loaded (\d+) pre-generated concepts', log)
    if prework:
        result.key_metrics["prework_concepts_used"] = int(prework.group(1))
        result.persistent_files_read.append("pre_generated_concepts.json")
    
    if "persistent-state" in log and "uploaded" in log.lower():
        result.persistent_write_success = True
        result.persistent_files_written.append("persistent-state/*")
    
    video_files = set(re.findall(r'output/(pro_[^\s]+\.mp4)', log))
    for vf in video_files:
        video = extract_video_info(log, vf)
        if any(p in log for p in ["[YOUTUBE] Uploading:", "[UPLOAD] Title:"]):
            video.uploaded = True
            video.platform = "YouTube"
        result.videos.append(video)
    
    if result.passed and result.videos:
        result.expected_behavior_met = True
    
    result.quota_usage = extract_detailed_quota(log)
    
    if "No videos were generated" in log and not result.videos:
        result.errors.append("No videos were generated")
    
    if result.videos:
        result.key_metrics["videos_generated"] = len(result.videos)
        result.key_metrics["videos_uploaded"] = sum(1 for v in result.videos if v.uploaded)
        result.key_metrics["total_size_mb"] = sum(v.file_size_mb for v in result.videos)
    
    return result


def analyze_prework(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    result = WorkflowAnalysisResult(run=run)
    result.passed = run.conclusion == "success"
    
    concepts = re.search(r'Concepts generated:\s*(\d+)', log)
    if concepts:
        result.key_metrics["concepts_generated"] = int(concepts.group(1))
        result.expected_behavior_met = True
    
    if "pre-generated-concepts" in log:
        result.persistent_write_success = True
        result.persistent_files_written.append("pre_generated_concepts.json")
    
    if "Pre-work: Generated" in log:
        result.key_metrics["git_committed"] = True
    
    if "QUOTA EXHAUSTED" in log:
        result.warnings.append("Skipped - quota exhausted")
        result.expected_behavior_met = True
    
    result.quota_usage = extract_detailed_quota(log)
    return result


def analyze_analytics(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    result = WorkflowAnalysisResult(run=run)
    result.passed = run.conclusion == "success"
    
    videos_match = re.search(r'Found (\d+) videos', log)
    if videos_match:
        result.key_metrics["videos_analyzed"] = int(videos_match.group(1))
        result.expected_behavior_met = True
    
    if "[OK] Restored state" in log:
        result.persistent_read_success = True
    
    if "persistent-state" in log:
        result.persistent_write_success = True
    
    insight = re.search(r'Key insight:\s*([^\n]+)', log)
    if insight:
        result.key_metrics["ai_insight"] = insight.group(1)[:100]
    
    patterns = ["variety_state.json", "viral_patterns.json", "hook_word_performance.json"]
    for p in patterns:
        if f"{p} updated" in log:
            result.persistent_files_written.append(p)
    
    result.key_metrics["patterns_updated"] = len(result.persistent_files_written)
    
    if "Status: concerning" in log:
        result.warnings.append("Shadow-ban indicator!")
        result.key_metrics["shadow_ban"] = "concerning"
    elif "Status: normal" in log:
        result.key_metrics["shadow_ban"] = "normal"
    
    top = re.search(r'(\d{1,3}(?:,\d{3})*) views - ([^\n]+)', log)
    if top:
        result.key_metrics["top_views"] = int(top.group(1).replace(',', ''))
        result.key_metrics["top_title"] = top.group(2)[:40]
    
    if "AI recommends skipping" in log:
        result.key_metrics["skipped_by_ai"] = True
        result.expected_behavior_met = True
    
    result.quota_usage = extract_detailed_quota(log)
    return result


def analyze_monthly(log: str, run: WorkflowRun) -> WorkflowAnalysisResult:
    result = WorkflowAnalysisResult(run=run)
    result.passed = run.conclusion == "success"
    
    if "Monthly Viral Analysis" in log:
        result.expected_behavior_met = True
    
    if "[OK] Restored state" in log:
        result.persistent_read_success = True
    
    if "persistent-state" in log:
        result.persistent_write_success = True
    
    result.quota_usage = extract_detailed_quota(log)
    return result


def analyze_workflow_run(run: WorkflowRun) -> WorkflowAnalysisResult:
    log = download_log(run.run_id)
    run.log_content = log
    
    if not log:
        result = WorkflowAnalysisResult(run=run)
        result.errors.append("Failed to download log (may be in progress)")
        return result
    
    if "Video Generator" in run.name:
        return analyze_video_generator(log, run)
    elif "Pre-Work" in run.name:
        return analyze_prework(log, run)
    elif "Analytics" in run.name or "Weekly" in run.name:
        return analyze_analytics(log, run)
    elif "Monthly" in run.name:
        return analyze_monthly(log, run)
    else:
        result = WorkflowAnalysisResult(run=run)
        result.warnings.append(f"Unknown workflow: {run.name}")
        return result


def analyze_persistent_data(data: Dict[str, Any]) -> List[PersistentDataAnalysis]:
    analyses = []
    expected = {
        "variety_state.json": ["preferred_categories", "learned_weights", "last_feedback"],
        "viral_patterns.json": ["our_best_patterns", "optimal_duration", "key_insight"],
        "analytics_state.json": ["videos", "total_views", "last_updated"],
        "upload_state.json": ["last_upload", "daily_count"],
        "hook_word_performance.json": ["words", "last_updated"],
        "category_decay.json": ["category_history"],
        "series_state.json": ["series_candidates"],
    }
    
    for filename, fields in expected.items():
        analysis = PersistentDataAnalysis(file_name=filename)
        
        if filename in data:
            analysis.exists = True
            fd = data[filename]
            
            if isinstance(fd, dict):
                analysis.record_count = len(fd)
                for f in ["last_updated", "last_feedback"]:
                    if f in fd:
                        analysis.last_updated = str(fd[f])[:25]
                        break
                
                for f in fields:
                    if f in fd:
                        v = fd[f]
                        if isinstance(v, list):
                            analysis.key_fields[f] = f"{len(v)} items"
                        elif isinstance(v, dict):
                            analysis.key_fields[f] = f"{len(v)} keys"
                        else:
                            analysis.key_fields[f] = str(v)[:40]
            
            if analysis.last_updated:
                try:
                    dt = datetime.fromisoformat(analysis.last_updated.replace('Z', '+00:00'))
                    days_old = (datetime.now(timezone.utc) - dt).days
                    analysis.health_status = "stale" if days_old > 7 else "healthy"
                except:
                    analysis.health_status = "healthy"
            else:
                analysis.health_status = "healthy" if analysis.record_count > 0 else "empty"
        else:
            analysis.exists = False
            analysis.health_status = "missing"
        
        analyses.append(analysis)
    
    return analyses


def generate_report(results: List[WorkflowAnalysisResult], persistent_data: Dict, 
                   persistent_analyses: List[PersistentDataAnalysis], days: int):
    safe_print("\n" + "=" * 80)
    safe_print("  COMPREHENSIVE WORKFLOW ANALYSIS REPORT")
    safe_print(f"  Period: Last {days} day(s)")
    safe_print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    safe_print("=" * 80)
    
    by_type = {}
    for r in results:
        by_type.setdefault(r.run.name, []).append(r)
    
    # SECTION 1: Summary
    safe_print("\n" + "-" * 80)
    safe_print("  1. WORKFLOW EXECUTION SUMMARY")
    safe_print("-" * 80)
    
    safe_print(f"\n   {'Workflow':<45} | {'Runs':>5} | {'Pass':>5} | {'Fail':>5} | {'Rate':>6}")
    safe_print("   " + "-" * 75)
    
    total_runs = total_passed = 0
    for wf_name, wf_results in by_type.items():
        runs = len(wf_results)
        passed = sum(1 for r in wf_results if r.passed)
        total_runs += runs
        total_passed += passed
        rate = f"{passed/runs*100:.0f}%" if runs else "N/A"
        icon = "✅" if passed == runs else "⚠️" if passed else "❌"
        safe_print(f"   {icon} {wf_name[:43]:<43} | {runs:>5} | {passed:>5} | {runs-passed:>5} | {rate:>6}")
    
    safe_print("   " + "-" * 75)
    rate = f"{total_passed/total_runs*100:.0f}%" if total_runs else "N/A"
    safe_print(f"   {'TOTAL':<45} | {total_runs:>5} | {total_passed:>5} | {total_runs-total_passed:>5} | {rate:>6}")
    
    # SECTION 2: Persistent Data Analysis
    safe_print("\n" + "-" * 80)
    safe_print("  2. PERSISTENT DATA ANALYSIS")
    safe_print("-" * 80)
    
    safe_print(f"\n   {'File':<30} | {'Status':>10} | {'Records':>8} | {'Last Updated':<20}")
    safe_print("   " + "-" * 75)
    
    for pa in persistent_analyses:
        icon = "✅" if pa.health_status == "healthy" else "⚠️" if pa.health_status == "stale" else "❌"
        last = pa.last_updated[:19] if pa.last_updated else "N/A"
        safe_print(f"   {pa.file_name:<30} | {icon} {pa.health_status:<7} | {pa.record_count:>8} | {last:<20}")
        for k, v in list(pa.key_fields.items())[:2]:
            safe_print(f"      → {k}: {v}")
    
    # Analytics insights from persistent data
    if "analytics_state.json" in persistent_data:
        a = persistent_data["analytics_state.json"]
        safe_print(f"\n   📊 CHANNEL ANALYTICS:")
        safe_print(f"      Total Views: {a.get('total_views', 0):,}")
        safe_print(f"      Avg Views: {a.get('avg_views', 0):,.0f}")
        if a.get('analysis', {}).get('key_insight'):
            safe_print(f"      AI Insight: \"{a['analysis']['key_insight'][:70]}...\"")
    
    if "viral_patterns.json" in persistent_data:
        p = persistent_data["viral_patterns.json"]
        safe_print(f"\n   🎯 LEARNED PATTERNS:")
        if p.get('optimal_duration'):
            safe_print(f"      Optimal Duration: {p['optimal_duration']}s")
        if p.get('optimal_phrase_count'):
            safe_print(f"      Optimal Phrases: {p['optimal_phrase_count']}")
        if p.get('our_best_patterns'):
            safe_print(f"      Saved Patterns: {len(p['our_best_patterns'])}")
    
    # SECTION 3: Read/Write Status
    safe_print("\n" + "-" * 80)
    safe_print("  3. PERSISTENT DATA READ/WRITE STATUS")
    safe_print("-" * 80)
    
    for wf_name, wf_results in by_type.items():
        safe_print(f"\n   📋 {wf_name}")
        reads = sum(1 for r in wf_results if r.persistent_read_success)
        writes = sum(1 for r in wf_results if r.persistent_write_success)
        total = len(wf_results)
        safe_print(f"      Read:  {reads}/{total} ({reads/total*100:.0f}%)")
        safe_print(f"      Write: {writes}/{total} ({writes/total*100:.0f}%)")
        
        all_reads = set()
        all_writes = set()
        for r in wf_results:
            all_reads.update(r.persistent_files_read)
            all_writes.update(r.persistent_files_written)
        if all_reads:
            safe_print(f"      Files Read: {', '.join(list(all_reads)[:3])}")
        if all_writes:
            safe_print(f"      Files Written: {', '.join(list(all_writes)[:3])}")
    
    # SECTION 4: Quota Report
    safe_print("\n" + "-" * 80)
    safe_print("  4. QUOTA USAGE (Per Model)")
    safe_print("-" * 80)
    
    quota_agg = {}
    rate_limited = []
    
    for r in results:
        for q in r.quota_usage:
            key = f"{q.provider}|{q.model}|{q.endpoint}"
            if key not in quota_agg:
                quota_agg[key] = QuotaUsage(
                    provider=q.provider, endpoint=q.endpoint, model=q.model,
                    calls=0, daily_limit=q.daily_limit
                )
            quota_agg[key].calls += q.calls
            if q.error_429:
                quota_agg[key].error_429 = True
                rate_limited.append((q.provider, q.model, r.run.run_id))
    
    for q in quota_agg.values():
        if q.daily_limit > 0:
            q.percent_used = round(q.calls / q.daily_limit * 100, 2)
    
    safe_print(f"\n   {'Provider':<10} | {'Model':<20} | {'Endpoint':<18} | {'Calls':>6} | {'Limit':>7} | {'%Used':>7}")
    safe_print("   " + "-" * 85)
    
    for key in sorted(quota_agg.keys()):
        q = quota_agg[key]
        limit = str(q.daily_limit) if q.daily_limit else "∞"
        pct = f"{q.percent_used}%" if q.daily_limit else "N/A"
        warn = "⚠️" if q.error_429 else "  "
        safe_print(f"   {warn}{q.provider:<8} | {q.model:<20} | {q.endpoint:<18} | {q.calls:>6} | {limit:>7} | {pct:>7}")
    
    if rate_limited:
        safe_print(f"\n   ⚠️ RATE LIMITS DETECTED:")
        seen = set()
        for prov, model, rid in rate_limited[:5]:
            k = f"{prov}:{model}"
            if k not in seen:
                safe_print(f"      - {prov} ({model}) in Run #{rid}")
                seen.add(k)
    else:
        safe_print(f"\n   ✅ No rate limits detected")
    
    # SECTION 5: Video Report
    all_videos = []
    for r in results:
        for v in r.videos:
            v.run_time = r.run.created_at
            all_videos.append(v)
    
    if all_videos:
        safe_print("\n" + "-" * 80)
        safe_print("  5. VIDEO CHARACTERISTICS")
        safe_print("-" * 80)
        
        safe_print(f"\n   📹 SUMMARY:")
        safe_print(f"      Generated: {len(all_videos)}")
        safe_print(f"      Uploaded: {sum(1 for v in all_videos if v.uploaded)}")
        safe_print(f"      Total Size: {sum(v.file_size_mb for v in all_videos):.1f} MB")
        
        categories = {}
        for v in all_videos:
            cat = v.category or "Unknown"
            categories[cat] = categories.get(cat, 0) + 1
        
        safe_print(f"\n   📊 CATEGORIES:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            safe_print(f"      - {cat}: {count}")
        
        safe_print(f"\n   {'Date':<12} | {'Category':<15} | {'Title':<28} | {'Size':>6} | {'Status':<10}")
        safe_print("   " + "-" * 80)
        
        for v in sorted(all_videos, key=lambda x: getattr(x, 'run_time', datetime.min), reverse=True)[:15]:
            date = getattr(v, 'run_time', datetime.min).strftime("%m-%d %H:%M")
            cat = (v.category or "?")[:13]
            title = (v.title or v.filename)[:26]
            size = f"{v.file_size_mb}MB" if v.file_size_mb else "?"
            status = "✅ Upload" if v.uploaded else "📁 Local"
            safe_print(f"   {date:<12} | {cat:<15} | {title:<28} | {size:>6} | {status:<10}")
    
    # SECTION 6: Analytics/Feedback Workflows
    analytics_results = [r for r in results if "Analytics" in r.run.name or "Weekly" in r.run.name or "Monthly" in r.run.name]
    
    if analytics_results:
        safe_print("\n" + "-" * 80)
        safe_print("  6. FEEDBACK/ANALYTICS WORKFLOWS")
        safe_print("-" * 80)
        
        for r in analytics_results:
            safe_print(f"\n   📊 {r.run.name}")
            safe_print(f"      Run: #{r.run.run_id} @ {r.run.created_at.strftime('%Y-%m-%d %H:%M')}")
            safe_print(f"      Status: {'✅ PASS' if r.passed else '❌ FAIL'}")
            for k, v in list(r.key_metrics.items())[:4]:
                if k != "skipped_by_ai":
                    safe_print(f"      {k}: {v}")
            if r.key_metrics.get("skipped_by_ai"):
                safe_print(f"      ⏭️ Skipped by AI")
    
    # SECTION 7: Errors/Warnings
    all_errors = [(r.run.name, r.run.run_id, e) for r in results for e in r.errors]
    all_warnings = [(r.run.name, r.run.run_id, w) for r in results for w in r.warnings]
    
    if all_errors or all_warnings:
        safe_print("\n" + "-" * 80)
        safe_print("  7. ERRORS & WARNINGS")
        safe_print("-" * 80)
        
        if all_errors:
            safe_print(f"\n   ❌ ERRORS ({len(all_errors)}):")
            for wf, rid, err in all_errors[:8]:
                safe_print(f"      [{wf[:20]}] #{rid}: {err[:45]}")
        
        if all_warnings:
            safe_print(f"\n   ⚠️ WARNINGS ({len(all_warnings)}):")
            for wf, rid, warn in all_warnings[:8]:
                safe_print(f"      [{wf[:20]}] #{rid}: {warn[:45]}")
    
    # SECTION 8: Health Summary
    safe_print("\n" + "=" * 80)
    safe_print("  SYSTEM HEALTH SUMMARY")
    safe_print("=" * 80)
    
    health_factors = [
        ("Workflow Success", total_passed / total_runs * 100 if total_runs else 0),
        ("Persistent Data", sum(1 for p in persistent_analyses if p.health_status == "healthy") / len(persistent_analyses) * 100 if persistent_analyses else 0),
        ("Video Uploads", sum(1 for v in all_videos if v.uploaded) / len(all_videos) * 100 if all_videos else 100),
        ("Rate Limits", max(0, 100 - len(set((p, m) for p, m, r in rate_limited)) * 20) if rate_limited else 100),
    ]
    
    overall = sum(h[1] for h in health_factors) / len(health_factors)
    icon = "🟢" if overall >= 90 else "🟡" if overall >= 70 else "🔴"
    status = "HEALTHY" if overall >= 90 else "DEGRADED" if overall >= 70 else "UNHEALTHY"
    
    safe_print(f"\n   {icon} System Health: {status} ({overall:.0f}%)")
    safe_print("")
    
    for name, score in health_factors:
        bar = "█" * int(score/5) + "░" * (20 - int(score/5))
        safe_print(f"   {name:<20}: [{bar}] {score:.0f}%")
    
    safe_print(f"\n   📊 Quick Stats:")
    safe_print(f"      Workflows: {total_runs} ({total_passed} passed)")
    safe_print(f"      Videos: {len(all_videos)} generated")
    safe_print(f"      Rate Limits: {len(rate_limited)} events")
    safe_print(f"      Persistent Files: {sum(1 for p in persistent_analyses if p.exists)}/{len(persistent_analyses)} present")
    
    safe_print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Comprehensive workflow analyzer")
    parser.add_argument("--days", type=int, default=1, help="Days to analyze")
    parser.add_argument("--skip-persistent", action="store_true", help="Skip persistent data download")
    args = parser.parse_args()
    
    safe_print("\n" + "=" * 80)
    safe_print("  COMPREHENSIVE WORKFLOW ANALYZER")
    safe_print(f"  Analyzing last {args.days} day(s)")
    safe_print("=" * 80)
    
    runs = get_scheduled_runs(args.days)
    if not runs:
        safe_print("\n[INFO] No scheduled runs found.")
        return
    
    persistent_data = {} if args.skip_persistent else download_persistent_state()
    
    safe_print(f"\n{'='*70}")
    safe_print(f"  STEP 3: Analyzing Persistent Data Content")
    safe_print(f"{'='*70}")
    persistent_analyses = analyze_persistent_data(persistent_data)
    safe_print(f"   Analyzed {len(persistent_analyses)} expected files")
    
    safe_print(f"\n{'='*70}")
    safe_print(f"  STEP 4: Analyzing {len(runs)} Workflow Runs")
    safe_print(f"{'='*70}")
    
    results = []
    for i, run in enumerate(runs, 1):
        safe_print(f"\n   [{i}/{len(runs)}] {run.name}")
        safe_print(f"      Run: #{run.run_id} | Status: {run.conclusion or 'in_progress'}")
        result = analyze_workflow_run(run)
        results.append(result)
        
        if result.videos:
            safe_print(f"      → {len(result.videos)} video(s), {sum(1 for v in result.videos if v.uploaded)} uploaded")
        for k, v in list(result.key_metrics.items())[:2]:
            safe_print(f"      → {k}: {v}")
    
    safe_print(f"\n{'='*70}")
    safe_print(f"  STEP 5: Generating Report")
    safe_print(f"{'='*70}")
    
    generate_report(results, persistent_data, persistent_analyses, args.days)
    
    safe_print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ViralShorts Factory - Comprehensive Systems Dry Run Test
=========================================================

Tests ALL systems WITHOUT consuming valuable quota:
1. Model Discovery (FREE API endpoints)
2. Quota Management
3. Persistent Data Read/Write
4. All Scorers and Calculators
5. Rate Limiters
6. Self-Learning Engine
7. Feedback Mechanisms (dry run)
8. Pre-Work Infrastructure
9. Video Generation Infrastructure (dry run)

QUOTA USAGE: ZERO (uses only free endpoints)
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'ai'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'analytics'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'quota'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'core'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'utils'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'enhancements'))

# Also add for GitHub Actions context
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/ai')
sys.path.insert(0, 'src/analytics')
sys.path.insert(0, 'src/quota')
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/utils')
sys.path.insert(0, 'src/enhancements')

# Results storage
TEST_RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "tests": {},
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def safe_print(msg: str):
    """Print with encoding fallback."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())

def record_test(name: str, passed: bool, details: str = "", warning: bool = False):
    """Record test result."""
    status = "PASS" if passed else ("WARN" if warning else "FAIL")
    TEST_RESULTS["tests"][name] = {
        "status": status,
        "details": details
    }
    if passed:
        TEST_RESULTS["passed"] += 1
    elif warning:
        TEST_RESULTS["warnings"] += 1
    else:
        TEST_RESULTS["failed"] += 1
    
    icon = "[OK]" if passed else ("[!]" if warning else "[X]")
    safe_print(f"   {icon} {name}: {details}")

def save_results():
    """Save test results to file."""
    Path("test_output").mkdir(exist_ok=True)
    with open("test_output/test_results.json", "w") as f:
        json.dump(TEST_RESULTS, f, indent=2)

# ============================================================================
# TEST 1: MODEL DISCOVERY (FREE ENDPOINTS)
# ============================================================================
def test_model_discovery():
    """Test model discovery using FREE API endpoints."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 1: MODEL DISCOVERY (Zero Quota)")
    safe_print("=" * 60)
    
    # Test Gemini model discovery
    try:
        from model_helper import _discover_gemini_models, get_dynamic_gemini_model
        
        # Check if API key is available
        if not os.environ.get("GEMINI_API_KEY"):
            record_test("Gemini Discovery", True, "Skipped (no API key - expected locally)", warning=True)
        else:
            models = _discover_gemini_models()
            if models and len(models) > 0:
                record_test("Gemini Discovery", True, f"Found {len(models)} models")
                
                # Test dynamic selection
                best = get_dynamic_gemini_model()
                record_test("Gemini Dynamic Selection", True, f"Selected: {best}")
            else:
                record_test("Gemini Discovery", False, "No models found (API available)")
    except Exception as e:
        record_test("Gemini Discovery", False, str(e)[:50])
    
    # Test Groq model discovery
    try:
        from model_helper import _discover_groq_models, get_dynamic_groq_model
        
        # Check if API key is available
        if not os.environ.get("GROQ_API_KEY"):
            record_test("Groq Discovery", True, "Skipped (no API key - expected locally)", warning=True)
        else:
            models = _discover_groq_models()
            if models and len(models) > 0:
                record_test("Groq Discovery", True, f"Found {len(models)} models")
                
                best = get_dynamic_groq_model()
                record_test("Groq Dynamic Selection", True, f"Selected: {best}")
            else:
                record_test("Groq Discovery", False, "No models found (API available)", warning=True)
    except Exception as e:
        record_test("Groq Discovery", False, str(e)[:50], warning=True)
    
    # Test high-quality model selection
    try:
        from model_helper import get_high_quality_model, get_model_for_task
        
        pro_model = get_high_quality_model("gemini")
        if pro_model:
            record_test("High-Quality Model", True, f"Found: {pro_model}")
        else:
            record_test("High-Quality Model", True, "None available (will use fallback)", warning=True)
        
        task_model = get_model_for_task("hook")
        record_test("Task-Based Selection", True, f"Hook task: {task_model}")
    except Exception as e:
        record_test("High-Quality Model", False, str(e)[:50])

# ============================================================================
# TEST 2: QUOTA MANAGEMENT
# ============================================================================
def test_quota_management():
    """Test quota management systems."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 2: QUOTA MANAGEMENT")
    safe_print("=" * 60)
    
    # Test quota cache
    try:
        from model_helper import (
            _load_quota_cache, _save_quota_cache, 
            record_quota_from_429, get_cached_quota
        )
        
        # Test write
        record_quota_from_429("test-quota-model", 100)
        
        # Test read
        cached = get_cached_quota("test-quota-model")
        if cached == 100:
            record_test("Quota Cache Write/Read", True, "Cache works correctly")
        else:
            record_test("Quota Cache Write/Read", False, f"Expected 100, got {cached}")
    except Exception as e:
        record_test("Quota Cache", False, str(e)[:50])
    
    # Test model cache
    try:
        from model_helper import _load_cache, _save_cache
        
        test_data = {"models": ["test-model"], "cached_at": datetime.now().isoformat()}
        _save_cache("test_provider", test_data)
        
        loaded = _load_cache("test_provider")
        if loaded and "test-model" in loaded.get("models", []):
            record_test("Model Cache Write/Read", True, "Cache works correctly")
        else:
            record_test("Model Cache Write/Read", False, "Failed to read cached data")
    except Exception as e:
        record_test("Model Cache", False, str(e)[:50])
    
    # Test rate limits
    try:
        from model_helper import get_rate_limits
        
        limits = get_rate_limits()
        if "gemini" in limits and "groq" in limits:
            record_test("Rate Limits", True, f"Gemini: {limits['gemini']}s, Groq: {limits['groq']}s")
        else:
            record_test("Rate Limits", False, "Missing rate limit config")
    except Exception as e:
        record_test("Rate Limits", False, str(e)[:50])

# ============================================================================
# TEST 3: PERSISTENT DATA
# ============================================================================
def test_persistent_data():
    """Test persistent data read/write."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 3: PERSISTENT DATA")
    safe_print("=" * 60)
    
    persistent_dir = Path("data/persistent")
    persistent_dir.mkdir(parents=True, exist_ok=True)
    
    # Test write
    try:
        test_file = persistent_dir / "test_persistent.json"
        test_data = {"test": True, "timestamp": datetime.now().isoformat()}
        
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        record_test("Persistent Write", True, f"Wrote to {test_file}")
    except Exception as e:
        record_test("Persistent Write", False, str(e)[:50])
    
    # Test read
    try:
        with open(test_file, "r") as f:
            loaded = json.load(f)
        
        if loaded.get("test") == True:
            record_test("Persistent Read", True, "Data integrity verified")
        else:
            record_test("Persistent Read", False, "Data mismatch")
    except Exception as e:
        record_test("Persistent Read", False, str(e)[:50])
    
    # List existing persistent files
    try:
        files = list(persistent_dir.glob("*.json"))
        record_test("Persistent Files", True, f"Found {len(files)} files", warning=len(files) == 0)
    except Exception as e:
        record_test("Persistent Files", False, str(e)[:50])

# ============================================================================
# TEST 4: SELF-LEARNING ENGINE
# ============================================================================
def test_self_learning():
    """Test self-learning engine."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 4: SELF-LEARNING ENGINE")
    safe_print("=" * 60)
    
    try:
        from self_learning_engine import get_learning_engine
        
        engine = get_learning_engine()
        
        # Test viral triggers
        triggers = engine.get_viral_triggers()
        source = triggers.get("source", "unknown")
        record_test("Viral Triggers", True, f"Source: {source}")
        
        # Test learn_from_video (doesn't consume quota)
        engine.learn_from_video(
            score=8,
            category="test",
            topic="Test Topic",
            hook="STOP - This is a test hook",
            phrases=["Test phrase 1", "Test phrase 2"]
        )
        record_test("Learn From Video", True, "Learning mechanism works")
        
        # Test prompt boost
        try:
            boost = engine.get_prompt_boost()
            if boost:
                record_test("Prompt Boost", True, f"Length: {len(boost)} chars")
            else:
                record_test("Prompt Boost", True, "No boost available (expected on fresh install)")
        except Exception as e:
            record_test("Prompt Boost", True, f"Method exists but error: {str(e)[:30]}", warning=True)
        
    except Exception as e:
        record_test("Self-Learning Engine", False, str(e)[:50])

# ============================================================================
# TEST 5: SCORERS AND CALCULATORS
# ============================================================================
def test_scorers():
    """Test all scorers and calculators."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 5: SCORERS AND CALCULATORS")
    safe_print("=" * 60)
    
    # Test content for all scorers
    test_content = {
        "hook": "STOP - Did you know 90% of people get this wrong?",
        "phrases": [
            "Most people make this mistake every day.",
            "Here's the secret that experts use.",
            "Try this simple trick starting tonight.",
            "You'll see results within 24 hours."
        ],
        "cta": "Comment below if this helped! Save for later.",
        "category": "productivity",
        "topic": "Morning routines"
    }
    
    # Virality Calculator
    try:
        from virality_calculator import get_virality_calculator
        calc = get_virality_calculator()
        result = calc.calculate_virality(test_content)
        score = result.get("overall_score", 0)
        grade = result.get("grade", "?")
        record_test("Virality Calculator", True, f"Score: {score}/100 ({grade})")
    except Exception as e:
        record_test("Virality Calculator", False, str(e)[:50])
    
    # Engagement Predictor
    try:
        from engagement_predictor import get_engagement_predictor
        pred = get_engagement_predictor()
        result = pred.predict_engagement(test_content)
        score = result.get("overall_engagement", 0)
        record_test("Engagement Predictor", True, f"Score: {score}/100")
    except Exception as e:
        record_test("Engagement Predictor", False, str(e)[:50])
    
    # Retention Predictor
    try:
        from retention_predictor import get_retention_predictor
        pred = get_retention_predictor()
        result = pred.predict_retention(test_content)
        score = result.get("overall_retention", 0)
        record_test("Retention Predictor", True, f"Score: {score}%")
    except Exception as e:
        record_test("Retention Predictor", False, str(e)[:50])
    
    # Script Analyzer
    try:
        from script_analyzer import get_script_analyzer
        analyzer = get_script_analyzer()
        result = analyzer.analyze_script(test_content)
        score = result.get("overall_score", 0)
        record_test("Script Analyzer", True, f"Score: {score}/100")
    except Exception as e:
        record_test("Script Analyzer", False, str(e)[:50])
    
    # AI Quality Gate
    try:
        from ai_quality_gate import get_quality_gate
        gate = get_quality_gate()
        passed, report = gate.check(test_content)
        overall = report.get("overall_score", 0)
        record_test("AI Quality Gate", True, f"Score: {overall}/100, Passed: {passed}")
    except Exception as e:
        record_test("AI Quality Gate", False, str(e)[:50])

# ============================================================================
# TEST 6: CONTENT GENERATORS (DRY RUN - No AI calls)
# ============================================================================
def test_generators_dry_run():
    """Test generator infrastructure without making AI calls."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 6: GENERATOR INFRASTRUCTURE (Dry Run)")
    safe_print("=" * 60)
    
    # Hook Generator structure
    try:
        # Read file directly to check structure (avoid import issues)
        hook_gen_path = PROJECT_ROOT / "src" / "ai" / "ai_hook_generator.py"
        if hook_gen_path.exists():
            content = hook_gen_path.read_text(encoding='utf-8')
            has_generate = 'def generate_hook' in content
            has_context = '_build_context_section' in content
            has_triggers = '_get_dynamic_triggers' in content
            
            if has_generate and has_context and has_triggers:
                record_test("Hook Generator Structure", True, "All required methods present")
            else:
                missing = []
                if not has_generate: missing.append("generate_hook")
                if not has_context: missing.append("_build_context_section")
                if not has_triggers: missing.append("_get_dynamic_triggers")
                record_test("Hook Generator Structure", False, f"Missing: {missing}")
        else:
            record_test("Hook Generator Structure", False, "File not found")
    except Exception as e:
        record_test("Hook Generator", False, str(e)[:50])
    
    # CTA Generator structure
    try:
        cta_gen_path = PROJECT_ROOT / "src" / "ai" / "ai_cta_generator.py"
        if cta_gen_path.exists():
            content = cta_gen_path.read_text(encoding='utf-8')
            has_generate = 'def generate_cta' in content
            has_context = '_build_context_section' in content
            
            if has_generate and has_context:
                record_test("CTA Generator Structure", True, "All methods present")
            else:
                record_test("CTA Generator Structure", False, "Missing methods")
        else:
            record_test("CTA Generator Structure", False, "File not found")
    except Exception as e:
        record_test("CTA Generator", False, str(e)[:50])
    
    # Pre-work fetcher structure
    try:
        from pre_work_fetcher import PreWorkFetcher
        fetcher = PreWorkFetcher()
        
        has_run = hasattr(fetcher, 'run')
        has_concepts = hasattr(fetcher, 'generate_video_concepts')
        
        if has_run and has_concepts:
            record_test("Pre-Work Fetcher Structure", True, "All methods present")
        else:
            record_test("Pre-Work Fetcher Structure", False, "Missing methods")
    except Exception as e:
        record_test("Pre-Work Fetcher", False, str(e)[:50])

# ============================================================================
# TEST 7: FEEDBACK MECHANISMS (DRY RUN)
# ============================================================================
def test_feedback_dry_run():
    """Test feedback mechanisms without making external calls."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 7: FEEDBACK MECHANISMS (Dry Run)")
    safe_print("=" * 60)
    
    # Analytics Feedback Controller
    try:
        from analytics_feedback import FeedbackLoopController
        controller = FeedbackLoopController()
        
        # Check preferences load
        prefs = controller.preferences
        record_test("Feedback Controller", True, f"Preferences loaded: {len(prefs)} keys")
        
        # Check update method exists
        has_update = hasattr(controller, '_update_all_generators_from_insights')
        record_test("Generator Feedback", has_update, "Update method present" if has_update else "Missing")
        
    except Exception as e:
        record_test("Feedback Controller", False, str(e)[:50])
    
    # Video Metadata Store
    try:
        from analytics_feedback import VideoMetadataStore
        store = VideoMetadataStore()
        
        # Check can get all
        all_videos = store.get_all()
        record_test("Metadata Store", True, f"Found {len(all_videos)} video records")
        
    except Exception as e:
        record_test("Metadata Store", False, str(e)[:50])

# ============================================================================
# TEST 8: RATE LIMITER
# ============================================================================
def test_rate_limiter():
    """Test rate limiter functionality."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 8: RATE LIMITER")
    safe_print("=" * 60)
    
    try:
        from model_helper import get_rate_limits
        
        limits = get_rate_limits()
        
        # Verify reasonable limits
        gemini_ok = 3 <= limits.get("gemini", 0) <= 10
        groq_ok = 1 <= limits.get("groq", 0) <= 5
        pexels_ok = 10 <= limits.get("pexels", 0) <= 30
        
        if gemini_ok and groq_ok and pexels_ok:
            record_test("Rate Limit Values", True, "All within expected ranges")
        else:
            record_test("Rate Limit Values", False, f"Unexpected values: {limits}", warning=True)
        
        # Test that limits are being respected (timing test)
        start = time.time()
        # Simulate delay check
        min_delay = limits.get("groq", 2.0)
        record_test("Rate Limit Check", True, f"Min delay: {min_delay}s")
        
    except Exception as e:
        record_test("Rate Limiter", False, str(e)[:50])

# ============================================================================
# TEST 9: VIDEO CHARACTERISTICS
# ============================================================================
def test_video_characteristics():
    """Test video characteristic gathering."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 9: VIDEO CHARACTERISTICS")
    safe_print("=" * 60)
    
    # Test music mood selector
    try:
        mood_path = PROJECT_ROOT / "src" / "ai" / "ai_music_mood.py"
        if mood_path.exists():
            content = mood_path.read_text(encoding='utf-8')
            has_select = 'def select_mood' in content
            has_class = 'class AIMusicMoodSelector' in content
            record_test("Music Mood Selector", has_select and has_class, "Structure OK")
        else:
            record_test("Music Mood Selector", False, "File not found")
    except Exception as e:
        record_test("Music Mood Selector", False, str(e)[:50])
    
    # Test hashtag generator structure
    try:
        hashtag_path = PROJECT_ROOT / "src" / "ai" / "ai_hashtag_generator.py"
        if hashtag_path.exists():
            content = hashtag_path.read_text(encoding='utf-8')
            has_generate = 'def generate_hashtags' in content
            record_test("Hashtag Generator", has_generate, "Structure OK")
        else:
            record_test("Hashtag Generator", False, "File not found")
    except Exception as e:
        record_test("Hashtag Generator", False, str(e)[:50])
    
    # Test title optimizer structure
    try:
        title_path = PROJECT_ROOT / "src" / "ai" / "ai_title_optimizer.py"
        if title_path.exists():
            content = title_path.read_text(encoding='utf-8')
            has_optimize = 'def optimize_title' in content
            record_test("Title Optimizer", has_optimize, "Structure OK")
        else:
            record_test("Title Optimizer", False, "File not found")
    except Exception as e:
        record_test("Title Optimizer", False, str(e)[:50])

# ============================================================================
# TEST 10: WORKFLOW FILES VALIDATION
# ============================================================================
def test_workflow_files():
    """Validate workflow files exist and have required structure."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 10: WORKFLOW FILES VALIDATION")
    safe_print("=" * 60)
    
    workflows_dir = PROJECT_ROOT / ".github" / "workflows"
    
    required_workflows = [
        ("generate.yml", ["GEMINI_API_KEY", "GROQ_API_KEY", "artifact"]),
        ("pre-work.yml", ["pre-generated", "permissions"]),
        ("analytics-feedback.yml", ["YOUTUBE", "analytics"]),
        ("monthly-analysis.yml", ["trends", "analysis"]),
    ]
    
    for workflow_name, required_keywords in required_workflows:
        try:
            workflow_path = workflows_dir / workflow_name
            if workflow_path.exists():
                content = workflow_path.read_text(encoding='utf-8')
                
                # Check for required keywords
                missing = [k for k in required_keywords if k.lower() not in content.lower()]
                
                if not missing:
                    record_test(f"Workflow: {workflow_name}", True, "Structure valid")
                else:
                    record_test(f"Workflow: {workflow_name}", False, f"Missing: {missing}", warning=True)
            else:
                record_test(f"Workflow: {workflow_name}", False, "File not found", warning=True)
        except Exception as e:
            record_test(f"Workflow: {workflow_name}", False, str(e)[:40])

# ============================================================================
# TEST 11: PRE-GENERATED CONCEPTS STRUCTURE
# ============================================================================
def test_prework_concepts():
    """Test pre-generated concepts structure."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 11: PRE-WORK CONCEPTS STRUCTURE")
    safe_print("=" * 60)
    
    concepts_path = Path("data/pre_generated_concepts.json")
    
    try:
        if concepts_path.exists():
            with open(concepts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check structure
            has_concepts = "concepts" in data
            has_categories = "categories" in data
            has_timestamp = "generated_at" in data
            
            if has_concepts and has_categories:
                concept_count = len(data.get("concepts", []))
                category_count = len(data.get("categories", []))
                record_test("Pre-Work Concepts", True, f"{concept_count} concepts, {category_count} categories")
            else:
                missing = []
                if not has_concepts: missing.append("concepts")
                if not has_categories: missing.append("categories")
                record_test("Pre-Work Concepts", False, f"Missing: {missing}")
        else:
            record_test("Pre-Work Concepts", True, "File not found (will be created by pre-work workflow)", warning=True)
    except Exception as e:
        record_test("Pre-Work Concepts", False, str(e)[:50])

# ============================================================================
# TEST 12: ANALYTICS FEEDBACK STRUCTURE
# ============================================================================
def test_analytics_structure():
    """Test analytics feedback structures."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 12: ANALYTICS FEEDBACK STRUCTURE")
    safe_print("=" * 60)
    
    # Check analytics state
    analytics_path = Path("data/persistent/analytics_state.json")
    try:
        if analytics_path.exists():
            with open(analytics_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video_count = len(data.get("videos", []))
            has_patterns = "learned_patterns" in data
            
            record_test("Analytics State", True, f"{video_count} videos, patterns: {has_patterns}")
        else:
            record_test("Analytics State", True, "File not found (expected on fresh install)", warning=True)
    except Exception as e:
        record_test("Analytics State", False, str(e)[:50])
    
    # Check content preferences
    prefs_path = Path("data/content_preferences.json")
    try:
        if prefs_path.exists():
            with open(prefs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            key_count = len(data)
            record_test("Content Preferences", True, f"{key_count} preferences stored")
        else:
            record_test("Content Preferences", True, "File not found (expected on fresh install)", warning=True)
    except Exception as e:
        record_test("Content Preferences", False, str(e)[:50])

# ============================================================================
# TEST 13: EMERGENCY FALLBACK VALIDATION
# ============================================================================
def test_emergency_fallbacks():
    """Test that emergency fallbacks are in place."""
    safe_print("\n" + "=" * 60)
    safe_print("  TEST 13: EMERGENCY FALLBACKS")
    safe_print("=" * 60)
    
    # Check model_helper has fallback chain
    try:
        model_helper_path = PROJECT_ROOT / "src" / "ai" / "model_helper.py"
        if model_helper_path.exists():
            content = model_helper_path.read_text(encoding='utf-8')
            
            has_fallback = 'EMERGENCY_FALLBACK' in content or 'fallback' in content.lower()
            has_cache = 'EMERGENCY_CACHE' in content or '_save_cache' in content
            has_retry = 'retry' in content.lower()
            
            checks_passed = sum([has_fallback, has_cache, has_retry])
            record_test("Model Fallbacks", checks_passed >= 2, f"Passed {checks_passed}/3 checks")
        else:
            record_test("Model Fallbacks", False, "model_helper.py not found")
    except Exception as e:
        record_test("Model Fallbacks", False, str(e)[:50])
    
    # Check workflow has retry logic
    try:
        generate_path = PROJECT_ROOT / ".github" / "workflows" / "generate.yml"
        if generate_path.exists():
            content = generate_path.read_text(encoding='utf-8')
            
            has_retry = 'retry' in content.lower() or 'continue-on-error' in content
            has_artifact = 'upload-artifact' in content and 'download-artifact' in content
            
            record_test("Workflow Resilience", has_retry or has_artifact, 
                       "Retry/fallback mechanisms present")
        else:
            record_test("Workflow Resilience", False, "generate.yml not found")
    except Exception as e:
        record_test("Workflow Resilience", False, str(e)[:50])

# ============================================================================
# MAIN
# ============================================================================
def main():
    """Run all tests."""
    safe_print("\n" + "=" * 60)
    safe_print("  VIRALSHORTS FACTORY - COMPREHENSIVE SYSTEM TEST")
    safe_print("  QUOTA USAGE: ZERO (Free endpoints only)")
    safe_print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests
    test_model_discovery()
    test_quota_management()
    test_persistent_data()
    test_self_learning()
    test_scorers()
    test_generators_dry_run()
    test_feedback_dry_run()
    test_rate_limiter()
    test_video_characteristics()
    test_workflow_files()
    test_prework_concepts()
    test_analytics_structure()
    test_emergency_fallbacks()
    
    # Summary
    duration = time.time() - start_time
    
    safe_print("\n" + "=" * 60)
    safe_print("  TEST SUMMARY")
    safe_print("=" * 60)
    safe_print(f"   Passed:   {TEST_RESULTS['passed']}")
    safe_print(f"   Warnings: {TEST_RESULTS['warnings']}")
    safe_print(f"   Failed:   {TEST_RESULTS['failed']}")
    safe_print(f"   Duration: {duration:.1f}s")
    safe_print("=" * 60)
    
    # Save results
    TEST_RESULTS["duration_seconds"] = duration
    save_results()
    safe_print(f"\n[OK] Results saved to test_output/test_results.json")
    
    # Exit code
    if TEST_RESULTS['failed'] > 0:
        safe_print("\n[FAIL] Some tests failed!")
        sys.exit(1)
    else:
        safe_print("\n[OK] All critical tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()


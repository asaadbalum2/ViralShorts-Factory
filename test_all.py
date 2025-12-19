#!/usr/bin/env python3
"""
Comprehensive Bug Check & Test Suite
"""

import sys
import os

print("=" * 60)
print("COMPREHENSIVE BUG CHECK")
print("=" * 60)

errors = []

# Test 1: Import all modules
print("\n[1] Testing imports...")

modules_to_test = [
    "platform_safety",
    "analytics_feedback",
    "viral_video_science",
    "ai_trend_detector",
    "god_tier_prompts",
    "dailymotion_uploader",
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"   OK {module}")
    except Exception as e:
        errors.append(f"{module}: {e}")
        print(f"   FAIL {module}: {e}")

# Test heavier modules
print("\n[2] Testing main modules...")

try:
    import script_v2
    print("   OK script_v2")
except Exception as e:
    errors.append(f"script_v2: {e}")
    print(f"   FAIL script_v2: {e}")

try:
    import generate_multi
    print("   OK generate_multi")
except Exception as e:
    errors.append(f"generate_multi: {e}")
    print(f"   FAIL generate_multi: {e}")

try:
    import dynamic_video_generator
    print("   OK dynamic_video_generator")
except Exception as e:
    errors.append(f"dynamic_video_generator: {e}")
    print(f"   FAIL dynamic_video_generator: {e}")

# Test 3: Check platform safety specs
print("\n[3] Testing platform safety...")
try:
    from platform_safety import PLATFORM_SPECS, AntiBanSystem
    system = AntiBanSystem()
    
    yt_res = PLATFORM_SPECS["youtube_shorts"]["resolution"]
    dm_res = PLATFORM_SPECS["dailymotion"]["resolution"]
    
    print(f"   YouTube Shorts resolution: {yt_res[0]}x{yt_res[1]}")
    print(f"   Dailymotion resolution: {dm_res[0]}x{dm_res[1]}")
    
    variations = system.get_unique_video_variations()
    print(f"   Video variations: {len(variations)} parameters")
    
    can_upload, reason = system.should_upload_now("youtube")
    print(f"   Upload check: {can_upload} - {reason}")
    
    title = system.generate_varied_title("Test Title")
    print(f"   Varied title: {title}")
    
    print("   OK platform_safety tests")
except Exception as e:
    errors.append(f"platform_safety test: {e}")
    print(f"   FAIL: {e}")

# Test 4: Check analytics
print("\n[4] Testing analytics feedback loop...")
try:
    from analytics_feedback import VideoMetadataStore, FeedbackLoopController
    
    controller = FeedbackLoopController()
    guidance = controller.get_content_guidance()
    print(f"   Content guidance: {len(guidance)} keys")
    
    store = VideoMetadataStore()
    print(f"   Metadata store: {len(store.metadata)} videos tracked")
    
    print("   OK analytics tests")
except Exception as e:
    errors.append(f"analytics test: {e}")
    print(f"   FAIL: {e}")

# Test 5: Check AI trend detection
print("\n[5] Testing AI trend detector...")
try:
    from ai_trend_detector import AITrendDetector, TrendingTopic
    
    detector = AITrendDetector()
    print("   AI Trend Detector initialized")
    
    # Don't actually call the API to save quota
    print("   (Skipping API call to save quota)")
    print("   OK ai_trend_detector")
except Exception as e:
    errors.append(f"ai_trend_detector test: {e}")
    print(f"   FAIL: {e}")

# Test 6: Check god tier prompts
print("\n[6] Testing god tier prompts...")
try:
    from god_tier_prompts import (
        VIRAL_TOPIC_PROMPT,
        BROLL_KEYWORDS_PROMPT,
        CONTENT_EVALUATION_PROMPT,
        VOICEOVER_PROMPT
    )
    
    print(f"   VIRAL_TOPIC_PROMPT: {len(VIRAL_TOPIC_PROMPT)} chars")
    print(f"   BROLL_KEYWORDS_PROMPT: {len(BROLL_KEYWORDS_PROMPT)} chars")
    print(f"   CONTENT_EVALUATION_PROMPT: {len(CONTENT_EVALUATION_PROMPT)} chars")
    print(f"   VOICEOVER_PROMPT: {len(VOICEOVER_PROMPT)} chars")
    
    print("   OK god_tier_prompts")
except Exception as e:
    errors.append(f"god_tier_prompts test: {e}")
    print(f"   FAIL: {e}")

# Test 7: Check video generation config
print("\n[7] Testing video generation config...")
try:
    from script_v2 import VIDEO_WIDTH, VIDEO_HEIGHT, THEMES
    
    print(f"   Video size: {VIDEO_WIDTH}x{VIDEO_HEIGHT}")
    print(f"   Themes available: {len(THEMES)}")
    
    # Check resolution matches platform specs
    from platform_safety import PLATFORM_SPECS
    expected_w, expected_h = PLATFORM_SPECS["youtube_shorts"]["resolution"]
    
    if VIDEO_WIDTH == expected_w and VIDEO_HEIGHT == expected_h:
        print(f"   Resolution matches YouTube Shorts: OK")
    else:
        errors.append(f"Resolution mismatch: {VIDEO_WIDTH}x{VIDEO_HEIGHT} vs {expected_w}x{expected_h}")
        print(f"   FAIL: Resolution mismatch!")
    
    print("   OK video config")
except Exception as e:
    errors.append(f"video config test: {e}")
    print(f"   FAIL: {e}")

# Summary
print("\n" + "=" * 60)
if errors:
    print(f"FOUND {len(errors)} ERRORS:")
    for err in errors:
        print(f"   - {err}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
    sys.exit(0)


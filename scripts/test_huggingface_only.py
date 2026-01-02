#!/usr/bin/env python3
"""
HuggingFace-Only Video Generation Test

Tests video generation using ONLY HuggingFace as the AI provider.
- No Gemini, Groq, or OpenRouter
- No regeneration attempts
- Full enhancement verification
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'quota'))

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('utf-8', errors='replace').decode('utf-8'))

def main():
    safe_print("=" * 60)
    safe_print("  HUGGINGFACE-ONLY TEST - ENHANCEMENT VERIFICATION")
    safe_print("=" * 60)
    safe_print("")
    
    # Track enhancements
    enhancements_checked = []
    
    # Override environment to force HuggingFace
    safe_print("[*] Forcing HuggingFace-only mode...")
    os.environ['GEMINI_API_KEY'] = ''  # Clear Gemini
    os.environ['GROQ_API_KEY'] = ''    # Clear Groq
    os.environ['OPENROUTER_API_KEY'] = ''  # Clear OpenRouter
    
    # Import the video generator
    from pro_video_generator import ProVideoGenerator
    
    safe_print("[1/8] Initializing Video Generator...")
    generator = ProVideoGenerator()
    
    # Force HuggingFace as primary
    generator.gemini_key = None
    generator.groq_key = None
    generator.openrouter_key = None
    generator.gemini_model = None
    generator.client = None
    generator.openrouter_available = False
    
    # Verify HuggingFace is available
    safe_print(f"[+] HuggingFace available: {generator.huggingface_available}")
    safe_print(f"[+] HuggingFace key: {'SET' if generator.huggingface_key else 'NOT SET'}")
    
    if not generator.huggingface_available:
        safe_print("[!] ERROR: HuggingFace key not available!")
        sys.exit(1)
    
    safe_print("")
    safe_print("[2/8] Testing HuggingFace Model Discovery...")
    try:
        from quota.quota_optimizer import get_quota_optimizer
        quota_opt = get_quota_optimizer()
        hf_models = quota_opt.get_huggingface_models(generator.huggingface_key, force_refresh=True)
        safe_print(f"[+] Found {len(hf_models)} HuggingFace models:")
        for m in hf_models[:5]:
            safe_print(f"    - {m}")
        enhancements_checked.append(("HuggingFace Dynamic Discovery", "PASS", f"{len(hf_models)} models found"))
    except Exception as e:
        safe_print(f"[!] Model discovery error: {e}")
        enhancements_checked.append(("HuggingFace Dynamic Discovery", "FAIL", str(e)))
    
    safe_print("")
    safe_print("[3/8] Testing AI Call with HuggingFace...")
    try:
        test_prompt = "Generate a single catchy topic for a viral YouTube Short about psychology. Just the topic, nothing else."
        result = generator.call_ai(test_prompt)
        if result:
            safe_print(f"[+] AI Response: {result[:100]}...")
            enhancements_checked.append(("HuggingFace AI Call", "PASS", result[:50]))
        else:
            safe_print("[!] AI call returned empty")
            enhancements_checked.append(("HuggingFace AI Call", "FAIL", "Empty response"))
    except Exception as e:
        safe_print(f"[!] AI call error: {e}")
        enhancements_checked.append(("HuggingFace AI Call", "FAIL", str(e)))
    
    safe_print("")
    safe_print("[4/8] Generating Video (NO REGENERATION)...")
    safe_print("-" * 60)
    
    # Generate the video
    try:
        category = os.environ.get('INPUT_CATEGORY', '') or None
        result = generator.generate_video(category=category, upload=False, max_regen=0)
        
        if result:
            safe_print("")
            safe_print("=" * 60)
            safe_print("  VIDEO GENERATED SUCCESSFULLY!")
            safe_print("=" * 60)
            safe_print(f"  Title: {result.get('title', 'N/A')}")
            safe_print(f"  Category: {result.get('category', 'N/A')}")
            safe_print(f"  Quality Score: {result.get('quality_score', 'N/A')}/10")
            safe_print(f"  Duration: {result.get('duration', 'N/A')}s")
            safe_print(f"  Video File: {result.get('video_path', 'N/A')}")
            
            enhancements_checked.append(("Video Generation", "PASS", f"Score: {result.get('quality_score', 'N/A')}/10"))
            
            # Check enhancement integration
            safe_print("")
            safe_print("[5/8] Verifying Enhancement Integration...")
            
            # Check v9 enhancements
            if hasattr(generator, 'enhancement_orch') and generator.enhancement_orch:
                safe_print("[+] Enhancement Orchestrator: ACTIVE")
                enhancements_checked.append(("Enhancement Orchestrator", "PASS", "Active"))
            else:
                safe_print("[!] Enhancement Orchestrator: NOT FOUND")
                enhancements_checked.append(("Enhancement Orchestrator", "FAIL", "Not initialized"))
            
            # Check learning engine
            if hasattr(generator, 'learning_engine') and generator.learning_engine:
                safe_print("[+] Self-Learning Engine: ACTIVE")
                enhancements_checked.append(("Self-Learning Engine", "PASS", "Active"))
            else:
                safe_print("[!] Self-Learning Engine: NOT FOUND")
                enhancements_checked.append(("Self-Learning Engine", "FAIL", "Not initialized"))
            
            # Check v12 enhancements
            if hasattr(generator, 'v12_enhancements') and generator.v12_enhancements:
                safe_print("[+] V12 Enhancements: ACTIVE")
                enhancements_checked.append(("V12 Enhancements", "PASS", "Active"))
            else:
                safe_print("[!] V12 Enhancements: NOT FOUND")
                enhancements_checked.append(("V12 Enhancements", "FAIL", "Not initialized"))
            
            # Check variety state
            variety_file = 'data/persistent/variety_state.json'
            if os.path.exists(variety_file):
                with open(variety_file) as f:
                    variety = json.load(f)
                safe_print(f"[+] Variety State: {len(variety)} keys loaded")
                enhancements_checked.append(("Variety State", "PASS", f"{len(variety)} keys"))
            else:
                safe_print("[!] Variety State: NOT FOUND")
                enhancements_checked.append(("Variety State", "INFO", "No previous state"))
            
            # Check viral patterns
            patterns_file = 'data/persistent/viral_patterns.json'
            if os.path.exists(patterns_file):
                with open(patterns_file) as f:
                    patterns = json.load(f)
                safe_print(f"[+] Viral Patterns: {len(patterns)} keys loaded")
                enhancements_checked.append(("Viral Patterns", "PASS", f"{len(patterns)} keys"))
            else:
                safe_print("[!] Viral Patterns: NOT FOUND")
                enhancements_checked.append(("Viral Patterns", "INFO", "No previous patterns"))
            
            safe_print("")
            safe_print("[6/8] Saving Video Metadata...")
            
            # Ensure test_output exists
            os.makedirs('test_output', exist_ok=True)
            
            # Save detailed metadata
            metadata = {
                "test_type": "huggingface_only",
                "timestamp": datetime.now().isoformat(),
                "provider_used": "HuggingFace",
                "result": result,
                "enhancements_checked": enhancements_checked,
                "quality_score": result.get('quality_score'),
                "regeneration_attempts": 0,
                "success": True
            }
            
            with open('test_output/video_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Copy video to test_output
            import shutil
            video_path = result.get('video_path')
            if video_path and os.path.exists(video_path):
                shutil.copy(video_path, 'test_output/')
                safe_print(f"[+] Video copied to test_output/")
            
        else:
            safe_print("[!] Video generation returned None")
            enhancements_checked.append(("Video Generation", "FAIL", "Returned None"))
            
    except Exception as e:
        import traceback
        safe_print(f"[!] Video generation error: {e}")
        traceback.print_exc()
        enhancements_checked.append(("Video Generation", "FAIL", str(e)))
    
    safe_print("")
    safe_print("[7/8] Enhancement Check Summary...")
    safe_print("-" * 60)
    safe_print(f"{'Enhancement':<35} {'Status':<8} {'Details'}")
    safe_print("-" * 60)
    for name, status, details in enhancements_checked:
        status_icon = "[OK]" if status == "PASS" else "[X]" if status == "FAIL" else "[i]"
        safe_print(f"{name:<35} {status_icon} {status:<6} {str(details)[:30]}")
    safe_print("-" * 60)
    
    passed = sum(1 for _, s, _ in enhancements_checked if s == "PASS")
    failed = sum(1 for _, s, _ in enhancements_checked if s == "FAIL")
    safe_print(f"Total: {passed} passed, {failed} failed")
    
    safe_print("")
    safe_print("[8/8] Test Complete!")
    safe_print("=" * 60)
    
    # Ensure test_output exists
    os.makedirs('test_output', exist_ok=True)
    
    # Save enhancement report
    with open('test_output/enhancement_report.json', 'w') as f:
        json.dump({
            "enhancements_checked": enhancements_checked,
            "passed": passed,
            "failed": failed,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


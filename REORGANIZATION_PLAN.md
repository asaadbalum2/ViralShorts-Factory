# ViralShorts Factory - Reorganization Plan

## Current State
- 100+ Python files in root directory
- Many temporary/recovery files
- No clear organization

## Proposed Structure

```
ViralShorts-Factory/
├── src/                          # Main source code
│   ├── core/                     # Core video generation
│   │   ├── __init__.py
│   │   ├── pro_video_generator.py
│   │   ├── video_renderer.py
│   │   └── video_enhancements.py
│   │
│   ├── ai/                       # AI-related modules
│   │   ├── __init__.py
│   │   ├── multi_ai.py
│   │   ├── god_tier_prompts.py
│   │   ├── ai_evaluator.py
│   │   ├── ai_generator.py
│   │   └── ai_trend_*.py
│   │
│   ├── enhancements/             # Enhancement systems
│   │   ├── __init__.py
│   │   ├── enhancements_v9.py
│   │   ├── enhancements_v12.py
│   │   └── critical_fixes.py
│   │
│   ├── analytics/                # Analytics & feedback
│   │   ├── __init__.py
│   │   ├── analytics_feedback.py
│   │   ├── self_learning_engine.py
│   │   └── viral_channel_analyzer.py
│   │
│   ├── quota/                    # Quota management
│   │   ├── __init__.py
│   │   ├── quota_optimizer.py
│   │   ├── quota_monitor.py
│   │   └── token_budget_manager.py
│   │
│   ├── platforms/                # Platform uploaders
│   │   ├── __init__.py
│   │   ├── youtube_uploader.py
│   │   ├── dailymotion_uploader.py
│   │   └── rumble_uploader.py
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── fetch_broll.py
│       ├── background_music.py
│       └── sound_effects.py
│
├── tests/                        # Test files
│   ├── test_*.py
│
├── scripts/                      # Helper scripts
│   ├── version_verification.py
│   ├── analyze_codebase.py
│   └── monthly_analysis.py
│
├── .github/                      # GitHub Actions
│   └── workflows/
│
├── data/                         # Persistent data
│   └── persistent/
│
├── assets/                       # Static assets
├── output/                       # Generated videos
├── cache/                        # Temporary cache
└── config/                       # Configuration

```

## Files to DELETE (temporary/recovery)

These files were created during chat recovery and are not needed:
- auto_fix_stuck_chat.py
- check_cursor_commands.py
- clear_cache_and_fix.py
- complete_chat_rebuild.py
- continue_project_now.py
- create_*.py (all chat creation files)
- deep_*.py
- emergency_*.py
- extract_*.py
- final_*.py (except final_check.py)
- find_*.py
- fix_*.py
- force_read_chat.py
- get_*.py
- investigate_*.py
- link_*.py
- load_*.py
- make_*.py
- nuclear_fix.py
- permanent_chat_fix.py
- read_*.py
- recover_*.py
- recreate_*.py
- restore_*.py
- verify_prompt_272_complete.py

## Files to DELETE (logs/temp)
- temp_log.txt
- workflow_log*.txt
- *.md (temporary docs, keep README.md)

## Steps to Execute

1. **Backup first**: `git stash` or commit current state
2. **Delete temporary files**
3. **Create directory structure**
4. **Move files to appropriate directories**
5. **Update all imports**
6. **Test everything works**
7. **Update workflows if needed**

## Risk
Moving files will break imports. Need to:
- Update all `from X import Y` statements
- Update all `import X` statements
- Test thoroughly before pushing



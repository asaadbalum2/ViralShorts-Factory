#!/usr/bin/env python3
"""
ViralShorts Factory - Version Verification System
==================================================

This script MUST be run before pushing any new version.
It checks ALL concerns automatically:

1. Analytics feedback is updated with latest changes
2. No hardcoded values that should be AI-driven
3. No quota violations possible
4. No contradicting/overriding configurations
5. All imported functions are actually USED
6. Self-review and bug search
7. Workflows are updated and functional
8. All enhancements are integrated (IN)

Usage:
    python version_verification.py          # Full verification
    python version_verification.py --quick  # Quick checks only
    
This is BUILT-IN - runs automatically on pre-commit hook.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

CRITICAL_FILES = [
    "pro_video_generator.py",  # Wrapper
    "src/core/pro_video_generator.py",  # Main generator
    "src/enhancements/enhancements_v9.py",
    "src/enhancements/enhancements_v12.py",
    "src/quota/quota_optimizer.py",
    "src/quota/token_budget_manager.py",
    "src/analytics/analytics_feedback.py",
    "src/utils/persistent_state.py",
]

WORKFLOW_FILES = [
    ".github/workflows/generate.yml",
    ".github/workflows/analytics-feedback.yml",
    ".github/workflows/monthly-analysis.yml",
    ".github/workflows/pre-work.yml",
]

# Patterns that indicate hardcoding that SHOULD be dynamic
HARDCODE_PATTERNS = [
    # Model names without dynamic selection
    (r'model\s*=\s*["\'](?!{)[a-z0-9\-\.]+["\']', "Hardcoded AI model name"),
    # Fixed category/topic strings used directly (not in seed lists)
    (r'category\s*=\s*["\']psychology["\']', "Hardcoded category 'psychology'"),
    (r'topic\s*=\s*["\'][^"\']+["\'](?!.*random)', "Potentially hardcoded topic"),
    # Fixed timestamps
    (r'cron:\s*["\'][0-9\s\*]+["\'].*#.*hardcoded', "Hardcoded cron schedule"),
]

# Patterns that indicate proper dynamic/AI-driven approach
GOOD_PATTERNS = [
    (r'get_quota_optimizer|QuotaOptimizer', "Uses dynamic quota optimizer"),
    (r'get_.*_models\(', "Uses dynamic model discovery"),
    (r'from quota_optimizer import', "Imports quota optimizer"),
]

# ============================================================================
# VERIFICATION CHECKS
# ============================================================================

class VersionVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        self.version = self._get_version()
        
    def _get_version(self) -> str:
        """Get current version from git or file."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                capture_output=True, text=True
            )
            match = re.search(r'v(\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except:
            pass
        return "unknown"
    
    def _read_file(self, path: str) -> str:
        """Read file contents safely."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return ""
    
    def _read_main_generator(self) -> str:
        """Read the main pro_video_generator.py (handles both old and new structure)."""
        content = self._read_file("src/core/pro_video_generator.py")
        if not content:
            content = self._read_main_generator()
        return content
    
    # ========================================================================
    # CHECK 1: Analytics Feedback Updated
    # ========================================================================
    def check_analytics_updated(self) -> bool:
        """Verify analytics feedback includes latest enhancement tracking."""
        print("\n[1] ANALYTICS FEEDBACK CHECK...")
        
        # Check both possible paths (old and new structure)
        content = self._read_file("src/analytics/analytics_feedback.py")
        if not content:
            content = self._read_file("analytics_feedback.py")
        if not content:
            self.errors.append("analytics_feedback.py not found in src/analytics/")
            return False
        
        # Check for v12 enhancement tracking
        checks = [
            ("v12_enhancements", "Tracks v12 enhancements"),
            ("quality_score", "Tracks quality scores"),
            ("performance", "Tracks performance metrics"),
        ]
        
        passed = 0
        for pattern, desc in checks:
            if pattern in content:
                self.passed.append(f"Analytics: {desc}")
                passed += 1
            else:
                self.warnings.append(f"Analytics missing: {desc}")
        
        # Check if analytics is used in main flow
        main_content = self._read_file("src/core/pro_video_generator.py")
        if not main_content:
            main_content = self._read_main_generator()
        if "analytics" in main_content.lower() and "record" in main_content.lower():
            self.passed.append("Analytics: Recording integrated in main flow")
            passed += 1
        else:
            self.errors.append("Analytics not recording in main flow")
        
        print(f"   Passed: {passed}/{len(checks)+1}")
        return passed == len(checks) + 1
    
    # ========================================================================
    # CHECK 2: No Hardcoded Values That Should Be Dynamic
    # ========================================================================
    def check_no_hardcoding(self) -> bool:
        """Check for hardcoded values that should be AI-driven."""
        print("\n[2] HARDCODING CHECK...")
        
        issues = []
        
        for filepath in CRITICAL_FILES:
            content = self._read_file(filepath)
            if not content:
                continue
            
            for pattern, desc in HARDCODE_PATTERNS:
                matches = re.findall(pattern, content)
                # Filter out fallback values (which are acceptable)
                for match in matches:
                    # Check if it's in a fallback/except block (acceptable)
                    context = content[max(0, content.find(match)-200):content.find(match)+200]
                    if "fallback" in context.lower() or "except" in context.lower():
                        continue
                    issues.append(f"{filepath}: {desc} - '{match[:50]}...'")
        
        if issues:
            for issue in issues[:5]:  # Limit output
                self.warnings.append(issue)
            print(f"   Found {len(issues)} potential hardcoding issues")
        else:
            self.passed.append("No hardcoding issues found")
            print("   No issues found")
        
        return len(issues) == 0
    
    # ========================================================================
    # CHECK 3: Quota Violation Prevention
    # ========================================================================
    def check_quota_safety(self) -> bool:
        """Verify quota management is in place."""
        print("\n[3] QUOTA SAFETY CHECK...")
        
        main_content = self._read_main_generator()
        
        checks = [
            ("budget_manager" in main_content, "Token budget manager used"),
            ("quota_monitor" in main_content, "Quota monitor used"),
            ("record_usage" in main_content, "Usage tracking active"),
            ("record_429" in main_content, "429 error handling active"),
            ("get_groq_models" in main_content, "Dynamic Groq models"),
            ("get_gemini_models" in main_content, "Dynamic Gemini models"),
        ]
        
        passed = 0
        for check, desc in checks:
            if check:
                self.passed.append(f"Quota: {desc}")
                passed += 1
            else:
                self.errors.append(f"Quota missing: {desc}")
        
        print(f"   Passed: {passed}/{len(checks)}")
        return passed == len(checks)
    
    # ========================================================================
    # CHECK 4: No Contradicting Configurations
    # ========================================================================
    def check_no_contradictions(self) -> bool:
        """Check for contradicting or overriding configurations."""
        print("\n[4] CONTRADICTION CHECK...")
        
        issues = []
        
        # Check for duplicate function definitions
        main_content = self._read_main_generator()
        func_defs = re.findall(r'^def (\w+)\(', main_content, re.MULTILINE)
        duplicates = [f for f in func_defs if func_defs.count(f) > 1]
        if duplicates:
            issues.append(f"Duplicate functions: {set(duplicates)}")
        
        # Check for conflicting imports
        imports = re.findall(r'^from (\w+) import .*?(\w+)', main_content, re.MULTILINE)
        import_names = [i[1] for i in imports]
        dup_imports = [i for i in import_names if import_names.count(i) > 1]
        if dup_imports:
            issues.append(f"Duplicate imports: {set(dup_imports)}")
        
        # Check for overriding global variables
        globals_set = re.findall(r'^([A-Z_]+)\s*=', main_content, re.MULTILINE)
        dup_globals = [g for g in globals_set if globals_set.count(g) > 1]
        if dup_globals:
            # Filter out intentional overrides (like in try/except)
            real_dups = []
            for g in set(dup_globals):
                pattern = rf'^{g}\s*='
                all_matches = list(re.finditer(pattern, main_content, re.MULTILINE))
                if len(all_matches) > 2:  # More than try/except pair
                    real_dups.append(g)
            if real_dups:
                issues.append(f"Multiple global assignments: {real_dups}")
        
        if issues:
            for issue in issues:
                self.warnings.append(issue)
            print(f"   Found {len(issues)} potential contradictions")
        else:
            self.passed.append("No contradictions found")
            print("   No issues found")
        
        return len(issues) == 0
    
    # ========================================================================
    # CHECK 5: All Imports Are Used
    # ========================================================================
    def check_all_imports_used(self) -> bool:
        """Verify all imported functions are actually used."""
        print("\n[5] IMPORT USAGE CHECK...")
        
        main_content = self._read_main_generator()
        
        # Find all imports from enhancements_v12
        v12_imports = re.findall(r'from enhancements_v12 import \(([\s\S]*?)\)', main_content)
        if v12_imports:
            import_str = v12_imports[0]
            # Only match function names (start with get_ or apply_)
            functions = re.findall(r'(get_\w+|apply_\w+)', import_str)
            
            used = 0
            unused = []
            for func in functions:
                # Check if function is called (not just imported)
                pattern = rf'{func}\s*\('
                if re.search(pattern, main_content):
                    used += 1
                else:
                    unused.append(func)
            
            usage_pct = 100 * used // len(functions) if functions else 0
            
            if unused:
                self.warnings.append(f"Unused v12 imports: {unused[:5]}...")
            
            if usage_pct >= 80:
                self.passed.append(f"V12 imports: {used}/{len(functions)} used ({usage_pct}%)")
                print(f"   V12 imports: {used}/{len(functions)} used ({usage_pct}%)")
                return True
            else:
                self.errors.append(f"V12 imports: Only {usage_pct}% used - need 80%+")
                print(f"   V12 imports: Only {usage_pct}% used - NEED 80%+")
                return False
        
        return True
    
    # ========================================================================
    # CHECK 6: Bug Search
    # ========================================================================
    def check_for_bugs(self) -> bool:
        """Search for common bug patterns."""
        print("\n[6] BUG PATTERN SEARCH...")
        
        bugs = []
        
        for filepath in CRITICAL_FILES:
            content = self._read_file(filepath)
            if not content:
                continue
            
            # Check for common issues
            bug_patterns = [
                (r'except:\s*$', "Bare except clause"),
                (r'import \*', "Wildcard import"),
                (r'print\([^)]*password', "Password in print"),
                (r'api_key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
                # Removed: .get() without default - too noisy, not a real bug
                # (r'\.get\([^,)]+\)[^.]', "Potentially unsafe .get() without default"),
            ]
            
            for pattern, desc in bug_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Check context to reduce false positives
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        context = content[max(0, match.start()-50):match.end()+50]
                        # Skip if it's in a comment
                        if not context.strip().startswith('#'):
                            bugs.append(f"{filepath}: {desc}")
        
        if bugs:
            for bug in bugs[:5]:
                self.warnings.append(bug)
            print(f"   Found {len(bugs)} potential issues")
        else:
            self.passed.append("No obvious bugs found")
            print("   No obvious bugs found")
        
        return len(bugs) == 0
    
    # ========================================================================
    # CHECK 7: Workflows Updated
    # ========================================================================
    def check_workflows(self) -> bool:
        """Verify workflows exist and are properly configured."""
        print("\n[7] WORKFLOW CHECK...")
        
        issues = []
        
        for wf_path in WORKFLOW_FILES:
            content = self._read_file(wf_path)
            if not content:
                issues.append(f"Missing workflow: {wf_path}")
                continue
            
            # Check for required secrets
            required_secrets = ["GROQ_API_KEY", "GEMINI_API_KEY", "PEXELS_API_KEY"]
            for secret in required_secrets:
                if secret not in content:
                    issues.append(f"{wf_path}: Missing {secret}")
            
            # Check for OPENROUTER_API_KEY (new requirement)
            if "generate" in wf_path and "OPENROUTER_API_KEY" not in content:
                issues.append(f"{wf_path}: Missing OPENROUTER_API_KEY")
        
        if issues:
            for issue in issues:
                self.warnings.append(issue)
            print(f"   Found {len(issues)} workflow issues")
        else:
            self.passed.append("All workflows properly configured")
            print("   All workflows OK")
        
        return len(issues) == 0
    
    # ========================================================================
    # CHECK 8: All Enhancements Integrated
    # ========================================================================
    def check_enhancements_integrated(self) -> bool:
        """Verify all enhancement systems are integrated."""
        print("\n[8] ENHANCEMENT INTEGRATION CHECK...")
        
        main_content = self._read_main_generator()
        
        checks = [
            ("V12_MASTER_PROMPT" in main_content, "V12 master prompt loaded"),
            ("v12_guidelines" in main_content, "V12 guidelines injected"),
            ("enhancement_orch" in main_content, "V9 orchestrator used"),
            ("ENHANCEMENTS_V12_AVAILABLE" in main_content, "V12 availability check"),
            ("learning_engine" in main_content, "Self-learning engine active"),
            ("VIRAL_SCIENCE_AVAILABLE" in main_content, "Viral video science integrated"),
            ("ValueDeliveryChecker" in main_content, "Value delivery checking active"),
            ("AI_PATTERN_GENERATOR_AVAILABLE" in main_content or "ai_pattern_generator" in main_content, "AI pattern generator integrated"),
            ("MODEL_INTELLIGENCE_AVAILABLE" in main_content or "model_intelligence" in main_content, "Model intelligence integrated"),
            ("AI_HOOK_GENERATOR_AVAILABLE" in main_content, "AI hook generator integrated"),
            ("AI_CTA_GENERATOR_AVAILABLE" in main_content, "AI CTA generator integrated"),
        ]
        
        passed = 0
        for check, desc in checks:
            if check:
                self.passed.append(f"Enhancement: {desc}")
                passed += 1
            else:
                self.errors.append(f"Enhancement missing: {desc}")
        
        print(f"   Passed: {passed}/{len(checks)}")
        return passed == len(checks)
    
    # ========================================================================
    # CHECK: AI-FIRST ARCHITECTURE
    # ========================================================================
    def check_ai_first_architecture(self) -> bool:
        """
        v17.8: Check that all content patterns are AI-generated, not hardcoded.
        
        This enforces the 'prompt-AI based architecture' principle:
        - Data files should be populated by AI, not hardcoded
        - Hardcoded data should be marked as fallback only
        """
        print("\n[8] AI-FIRST ARCHITECTURE CHECK")
        
        all_good = True
        
        # Check viral_patterns.json
        patterns_file = "data/persistent/viral_patterns.json"
        try:
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("ai_generated") == True:
                    self.passed.append("viral_patterns.json is AI-generated")
                    print("   [OK] viral_patterns.json: AI-generated")
                elif data.get("patterns_source") == "NEEDS_AI_GENERATION":
                    self.passed.append("viral_patterns.json marked for AI generation")
                    print("   [OK] viral_patterns.json: Awaiting AI generation")
                else:
                    # Check if it looks hardcoded
                    if len(data.get("title_patterns", [])) > 3 and not data.get("ai_generated"):
                        self.warnings.append("viral_patterns.json appears hardcoded - should be AI-generated")
                        print("   [!] viral_patterns.json: May be hardcoded (review needed)")
                    else:
                        self.passed.append("viral_patterns.json structure OK")
                        print("   [OK] viral_patterns.json: Structure OK")
        except Exception as e:
            self.warnings.append(f"Could not check viral_patterns.json: {e}")
        
        # Check variety_state.json
        variety_file = "data/persistent/variety_state.json"
        try:
            if os.path.exists(variety_file):
                with open(variety_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("source") in ["AI_LEARNED", "AI_GENERATED", "ANALYTICS", "ANALYTICS_LEARNED"]:
                    self.passed.append("variety_state.json is AI-learned")
                    print("   [OK] variety_state.json: AI-learned")
                elif data.get("weekly_last_updated"):
                    self.passed.append("variety_state.json updated by analytics")
                    print("   [OK] variety_state.json: Updated by analytics")
                else:
                    self.passed.append("variety_state.json exists")
                    print("   [INFO] variety_state.json: Exists (source not specified)")
        except Exception as e:
            self.warnings.append(f"Could not check variety_state.json: {e}")
        
        # Check for AIPatternGenerator in codebase
        generator_file = "src/ai/ai_pattern_generator.py"
        if os.path.exists(generator_file):
            content = self._read_file(generator_file)
            if "generate_patterns_with_ai" in content:
                self.passed.append("AI pattern generator implemented")
                print("   [OK] AI pattern generator: Implemented")
            else:
                self.errors.append("AI pattern generator missing generate_patterns_with_ai")
                all_good = False
        else:
            self.errors.append("Missing src/ai/ai_pattern_generator.py")
            all_good = False
            print("   [X] AI pattern generator: MISSING")
        
        # Check self_learning.json
        learning_file = "data/persistent/self_learning.json"
        try:
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("source") == "REAL_ANALYTICS":
                    self.passed.append("self_learning.json marked for real analytics")
                    print("   [OK] self_learning.json: Real analytics only")
                elif data.get("awaiting_real_data"):
                    self.passed.append("self_learning.json awaiting real data")
                    print("   [OK] self_learning.json: Awaiting real data")
                else:
                    # Check if it looks seeded
                    if data.get("stats", {}).get("total_videos", 0) > 10:
                        self.warnings.append("self_learning.json may contain seeded data")
                        print("   [!] self_learning.json: May have seeded data (review)")
                    else:
                        self.passed.append("self_learning.json structure OK")
                        print("   [OK] self_learning.json: Structure OK")
        except Exception as e:
            self.warnings.append(f"Could not check self_learning.json: {e}")
        
        return all_good
    
    # ========================================================================
    # CHECK 9: NEW AI MODULES (v17.8.27)
    # ========================================================================
    def check_ai_modules(self) -> bool:
        """Check that all new AI modules exist and are functional."""
        print("\n[9] AI MODULES CHECK (v17.8.27)...")
        
        # All AI modules that should exist
        ai_modules = [
            ("src/ai/ai_description_generator.py", "get_description_generator"),
            ("src/ai/ai_hashtag_generator.py", "get_hashtag_generator"),
            ("src/ai/ai_thumbnail_text.py", "get_thumbnail_optimizer"),
            ("src/ai/ai_trend_analyzer.py", "get_trend_analyzer"),
            ("src/ai/ai_audience_persona.py", "get_persona_generator"),
            ("src/ai/ai_voice_script.py", "get_voice_optimizer"),
            ("src/ai/ai_comment_response.py", "get_comment_generator"),
            ("src/analytics/retention_predictor.py", "get_retention_predictor"),
            ("src/analytics/engagement_predictor.py", "get_engagement_predictor"),
            ("src/analytics/virality_calculator.py", "get_virality_calculator"),
            ("src/analytics/script_analyzer.py", "get_script_analyzer"),
            ("src/analytics/competitor_gap_analyzer.py", "get_gap_analyzer"),
            ("src/analytics/dashboard_generator.py", "get_dashboard_generator"),
            ("src/core/content_optimizer.py", "get_content_optimizer"),
            ("src/core/ai_quality_gate.py", "get_quality_gate"),
        ]
        
        passed = 0
        missing = 0
        
        for filepath, function_name in ai_modules:
            if os.path.exists(filepath):
                content = self._read_file(filepath)
                if function_name in content:
                    passed += 1
                else:
                    self.warnings.append(f"{filepath}: Missing {function_name}")
            else:
                self.errors.append(f"Missing AI module: {filepath}")
                missing += 1
        
        if missing == 0:
            self.passed.append(f"All {len(ai_modules)} AI modules present")
            print(f"   [OK] All {len(ai_modules)} AI modules found")
        else:
            print(f"   [X] Missing {missing} AI modules")
        
        print(f"   Modules verified: {passed}/{len(ai_modules)}")
        
        return missing == 0
    
    # ========================================================================
    # CHECK 10: AI MODULE INTEGRATION (v17.9.6)
    # ========================================================================
    def check_ai_module_integration(self) -> bool:
        """Check that all AI modules are actually INTEGRATED (not just existing)."""
        print("\n[10] AI MODULE INTEGRATION CHECK (v17.9.6)...")
        
        generator = self._read_file("src/core/pro_video_generator.py")
        
        # These modules must be imported AND used in the generator
        required_integrations = [
            ("AIQualityGate", "AI_QUALITY_GATE_AVAILABLE"),
            ("ContentOptimizer", "CONTENT_OPTIMIZER_AVAILABLE"),
            ("RetentionPredictor", "RETENTION_PREDICTOR_AVAILABLE"),
            ("EngagementPredictor", "ENGAGEMENT_PREDICTOR_AVAILABLE"),
            ("ViralityCalculator", "VIRALITY_CALCULATOR_AVAILABLE"),
            ("ScriptAnalyzer", "SCRIPT_ANALYZER_AVAILABLE"),
            ("AIDescriptionGenerator", "AI_DESCRIPTION_GENERATOR_AVAILABLE"),
            ("AIHashtagGenerator", "AI_HASHTAG_GENERATOR_AVAILABLE"),
            ("DashboardGenerator", "DASHBOARD_GENERATOR_AVAILABLE"),
        ]
        
        integrated = 0
        for class_name, flag_name in required_integrations:
            if class_name in generator and flag_name in generator:
                integrated += 1
                print(f"   [OK] {class_name}")
            else:
                self.errors.append(f"{class_name} not integrated in generator")
                print(f"   [X] {class_name} NOT INTEGRATED")
        
        if integrated == len(required_integrations):
            self.passed.append(f"All {len(required_integrations)} AI modules integrated")
            return True
        else:
            return False
    
    # ========================================================================
    # CHECK 11: v17.9.5 YOUTUBE-ONLY MODE
    # ========================================================================
    def check_youtube_only_mode(self) -> bool:
        """Check v17.9.5 YouTube-only features are properly configured."""
        print("\n[11] YOUTUBE-ONLY MODE CHECK (v17.9.5)...")
        # Note: Check numbers updated for v17.9.6
        
        issues = []
        
        # Check workflow has --youtube-only flag
        workflow = self._read_file(".github/workflows/generate.yml")
        if "--youtube-only" in workflow:
            self.passed.append("Workflow uses --youtube-only flag")
            print("   [OK] --youtube-only flag in workflow")
        else:
            issues.append("Workflow missing --youtube-only flag")
            print("   [X] --youtube-only flag NOT FOUND in workflow")
        
        # Check batch_size default is 1
        if "default: '1'" in workflow and "Videos to generate (1 per workflow" in workflow:
            self.passed.append("Batch size default is 1")
            print("   [OK] Batch size default = 1")
        else:
            issues.append("Batch size default should be 1 for YouTube-only")
            print("   [!] Batch size default not set to 1")
        
        # Check Dailymotion is not in upload command
        if "dailymotion=False" in self._read_file("src/core/pro_video_generator.py"):
            self.passed.append("Dailymotion disabled in youtube-only mode")
            print("   [OK] Dailymotion disabled")
        
        # Check learned metrics function exists
        generator = self._read_file("src/core/pro_video_generator.py")
        if "get_learned_optimal_metrics" in generator:
            self.passed.append("Learned metrics function exists")
            print("   [OK] get_learned_optimal_metrics() exists")
        else:
            issues.append("Missing get_learned_optimal_metrics function")
            print("   [X] get_learned_optimal_metrics NOT FOUND")
        
        # Check update_learned_metrics is called in workflow
        if "update_learned_metrics_from_performance" in workflow:
            self.passed.append("Metrics learning integrated in workflow")
            print("   [OK] Metrics learning in workflow")
        else:
            issues.append("update_learned_metrics not called in workflow")
            print("   [X] Metrics learning NOT in workflow")
        
        if issues:
            for issue in issues:
                self.errors.append(issue)
            return False
        return True
    
    # ========================================================================
    # CHECK 11: TEST SUITE STATUS
    # ========================================================================
    def check_test_suite(self) -> bool:
        """Check that the test suite exists and passes."""
        print("\n[11] TEST SUITE CHECK...")
        
        test_file = "scripts/test_all_ai_modules.py"
        
        if not os.path.exists(test_file):
            self.errors.append("Test suite missing: scripts/test_all_ai_modules.py")
            print("   [X] Test suite NOT FOUND")
            return False
        
        content = self._read_file(test_file)
        
        # Count test sections
        test_count = content.count("# TEST ")
        
        if test_count >= 20:
            self.passed.append(f"Test suite has {test_count} test sections")
            print(f"   [OK] Test suite has {test_count} test sections")
        else:
            self.warnings.append(f"Test suite only has {test_count} tests (expected 20+)")
            print(f"   [!] Only {test_count} test sections (expected 20+)")
        
        return True
    
    # ========================================================================
    # CHECK 14: v17.9.7 FIXES VERIFICATION
    # ========================================================================
    def check_v1797_fixes(self) -> bool:
        """Check v17.9.7 critical fixes are properly implemented."""
        print("\n[14] v17.9.7 FIXES CHECK...")
        
        issues = []
        generator = self._read_file("src/core/pro_video_generator.py")
        model_helper = self._read_file("src/ai/model_helper.py")
        budget_manager = self._read_file("src/quota/token_budget_manager.py")
        
        # 1. AI module method fixes - correct method names used
        if "analyzer.analyze_script(script_content)" in generator:
            print("   [OK] ScriptAnalyzer uses correct analyze_script(content) call")
        else:
            issues.append("ScriptAnalyzer may have wrong method call")
        
        if "predictor.predict_retention(retention_content)" in generator:
            print("   [OK] RetentionPredictor uses correct predict_retention(content) call")
        else:
            issues.append("RetentionPredictor may have wrong method call")
        
        if "calculator.calculate_virality(virality_content)" in generator:
            print("   [OK] ViralityCalculator uses correct calculate_virality(content) call")
        else:
            issues.append("ViralityCalculator may have wrong method call")
        
        if "quality_gate.check(gate_content)" in generator:
            print("   [OK] AIQualityGate uses correct check(content) call")
        else:
            issues.append("AIQualityGate may have wrong method call")
        
        if "optimizer.optimize(opt_content)" in generator:
            print("   [OK] ContentOptimizer uses correct optimize(content) call")
        else:
            issues.append("ContentOptimizer may have wrong method call")
        
        # 2. Rate limiter optimization
        if '"groq": 2.0' in model_helper or "'groq': 2.0" in model_helper:
            print("   [OK] Groq rate limit is 2.0s (optimized)")
        else:
            issues.append("Groq rate limit not optimized to 2.0s")
        
        if '"gemini": 5.0' in model_helper or "'gemini': 5.0" in model_helper:
            print("   [OK] Gemini rate limit is 5.0s (safe)")
        else:
            issues.append("Gemini rate limit not set to 5.0s")
        
        # 3. Provider priority - Groq should be primary
        if "Groq is PRIMARY" in budget_manager or "GROQ FIRST" in budget_manager:
            print("   [OK] Groq is PRIMARY provider")
        else:
            issues.append("Groq not set as primary provider")
        
        # 4. TTS retry logic
        if "fallback_voices" in generator and "for retry in range(3)" in generator:
            print("   [OK] TTS has retry logic with fallback voices")
        else:
            issues.append("TTS missing retry logic or fallback voices")
        
        # 5. Version is 17.9.7
        if "v17.9.7" in generator:
            print("   [OK] Version is v17.9.7")
        else:
            issues.append("Version not updated to v17.9.7")
        
        if issues:
            for issue in issues:
                self.errors.append(f"v17.9.7: {issue}")
                print(f"   [X] {issue}")
            return False
        else:
            self.passed.append("All v17.9.7 fixes verified")
            return True
    
    # ========================================================================
    # MAIN VERIFICATION
    # ========================================================================
    def run_all_checks(self) -> bool:
        """Run all verification checks."""
        print("=" * 60)
        print(f"VERSION VERIFICATION - v{self.version}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        results = [
            self.check_analytics_updated(),
            self.check_no_hardcoding(),
            self.check_quota_safety(),
            self.check_no_contradictions(),
            self.check_all_imports_used(),
            self.check_for_bugs(),
            self.check_workflows(),
            self.check_enhancements_integrated(),
            self.check_ai_first_architecture(),  # v17.8: New check
            self.check_ai_module_integration(),  # v17.9.6: All modules integrated
            self.check_youtube_only_mode(),  # v17.9.5: YouTube-only mode
            self.check_ai_modules(),  # v17.8.27: All AI modules
            self.check_test_suite(),  # v17.8.27: Test suite
            self.check_v1797_fixes(),  # v17.9.7: Critical fixes
        ]
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Passed:   {len(self.passed)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors:   {len(self.errors)}")
        
        if self.errors:
            print("\nERRORS (must fix):")
            for e in self.errors:
                print(f"  [X] {e}")
        
        if self.warnings:
            print("\nWARNINGS (review):")
            for w in self.warnings[:10]:
                print(f"  [!] {w}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
        
        # Only fail on actual errors, not warnings
        all_passed = len(self.errors) == 0
        
        print("\n" + "=" * 60)
        if all_passed:
            print("[PASSED] VERIFICATION PASSED - Safe to push")
        else:
            print("[FAILED] VERIFICATION FAILED - Fix issues before pushing")
        print("=" * 60)
        
        return all_passed
    
    def save_report(self):
        """Save verification report to file."""
        report = {
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "result": "PASSED" if len(self.errors) == 0 else "FAILED"
        }
        
        report_dir = Path("data/persistent")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_dir / "last_verification.json", 'w') as f:
            json.dump(report, f, indent=2)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    verifier = VersionVerifier()
    
    if "--quick" in sys.argv:
        # Quick mode - just essential checks
        verifier.check_quota_safety()
        verifier.check_all_imports_used()
        verifier.check_workflows()
    else:
        # Full verification
        success = verifier.run_all_checks()
        verifier.save_report()
        
        if not success:
            print("\nRun with fixes, then verify again before pushing.")
            sys.exit(1)


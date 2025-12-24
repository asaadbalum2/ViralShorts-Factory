#!/usr/bin/env python3
"""
DEEP INVESTIGATION: Are enhancements actually used?
"""
import re

print('=' * 80)
print('DEEP INVESTIGATION: ARE ENHANCEMENTS ACTUALLY USED?')
print('=' * 80)

# Read the main generator
with open('pro_video_generator.py', 'r', encoding='utf-8') as f:
    gen_content = f.read()

# =============================================
# CHECK 1: Typography/Font - Is AI choice used?
# =============================================
print('\n[1] TYPOGRAPHY/FONT USAGE')
print('-' * 40)

# Find where fonts are set
font_hardcoded = re.findall(r'font\s*=\s*["\']([^"\']+)["\']', gen_content)
print(f'Hardcoded fonts found: {len(font_hardcoded)}')
for f in set(font_hardcoded):
    print(f'  - "{f}"')

# Check if AI font choice is used
if 'ai_font' in gen_content or 'font_choice' in gen_content or 'selected_font' in gen_content:
    print('AI font selection: FOUND')
else:
    print('AI font selection: NOT FOUND - FONTS ARE HARDCODED!')

# =============================================
# CHECK 2: Sound Effects - Are they varied?
# =============================================
print('\n[2] SOUND EFFECTS VARIETY')
print('-' * 40)

# Check how SFX are added
sfx_section = gen_content[gen_content.find('sound effect'):gen_content.find('sound effect')+2000] if 'sound effect' in gen_content else ''
if 'random.choice' in sfx_section:
    print('SFX randomization: FOUND in SFX section')
else:
    print('SFX randomization: NOT FOUND - SAME SFX PATTERN EVERY TIME!')

# Check what SFX are used
sfx_files = re.findall(r'sfx/(\w+)\.wav', gen_content)
print(f'SFX files referenced: {set(sfx_files)}')

# =============================================
# CHECK 3: Numbered Promise Rule - Is it enforced?
# =============================================
print('\n[3] NUMBERED PROMISE ENFORCEMENT')
print('-' * 40)

promise_in_code = 'promise' in gen_content.lower()
print(f'Promise word in code: {promise_in_code}')

# Check stage3 for promise check
stage3_start = gen_content.find('def stage3_evaluate')
stage3_end = gen_content.find('def stage4', stage3_start) if stage3_start > 0 else -1
if stage3_start > 0 and stage3_end > 0:
    stage3_content = gen_content[stage3_start:stage3_end]
    if 'promise' in stage3_content.lower() or 'PROMISE' in stage3_content:
        print('Promise check in stage3: FOUND in prompt')
    else:
        print('Promise check in stage3: NOT IN PROMPT!')
else:
    print('stage3_evaluate_enhance: NOT FOUND!')

# =============================================
# CHECK 4: v12 Master Prompt - Is it actually injected?
# =============================================
print('\n[4] V12 MASTER PROMPT INJECTION')
print('-' * 40)

v12_import = 'from enhancements_v12 import' in gen_content
print(f'v12 imported: {v12_import}')

v12_master_ref = gen_content.count('V12_MASTER_PROMPT')
print(f'V12_MASTER_PROMPT references: {v12_master_ref}')

v12_guidelines_ref = gen_content.count('v12_guidelines')
print(f'v12_guidelines references: {v12_guidelines_ref}')

# Check if v12_guidelines is in stage1 or stage2
stage1_start = gen_content.find('def stage1_decide')
stage2_start = gen_content.find('def stage2_create')
if stage1_start > 0 and stage2_start > 0:
    stage1_content = gen_content[stage1_start:stage2_start]
    if 'v12_guidelines' in stage1_content or 'V12' in stage1_content:
        print('v12 in stage1: YES')
    else:
        print('v12 in stage1: NO!')
        
    stage3_start_2 = gen_content.find('def stage3_evaluate', stage2_start)
    if stage3_start_2 > 0:
        stage2_content = gen_content[stage2_start:stage3_start_2]
        if 'v12_guidelines' in stage2_content or 'V12' in stage2_content:
            print('v12 in stage2: YES')
        else:
            print('v12 in stage2: NO!')

# =============================================
# CHECK 5: Quality Gate - Does it actually reject low scores?
# =============================================
print('\n[5] QUALITY GATE ENFORCEMENT')
print('-' * 40)

if 'evaluation_score' in gen_content:
    print('evaluation_score: TRACKED')
else:
    print('evaluation_score: NOT TRACKED!')

# Check if low scores cause regeneration or rejection
score_rejection_patterns = [
    r'score\s*<\s*\d',
    r'if.*score.*reject',
    r'MIN.*SCORE',
    r'minimum.*score'
]
found_rejection = False
for pattern in score_rejection_patterns:
    if re.search(pattern, gen_content, re.IGNORECASE):
        found_rejection = True
        print(f'Score rejection pattern found: {pattern}')
        break

if not found_rejection:
    print('Score rejection: NOT ENFORCED - ALL SCORES ACCEPTED!')

# =============================================
# CHECK 6: Are v12 functions actually CALLED?
# =============================================
print('\n[6] V12 FUNCTION CALLS IN GENERATOR')
print('-' * 40)

v12_functions = [
    'apply_v12_text_humanization',
    'get_v12_voice_settings',
    'get_v12_complete_master_prompt',
    'get_natural_rhythm',
    'get_filler_injector',
    'get_font_psychology',
    'get_color_grading',
    'get_fomo_trigger'
]

for func in v12_functions:
    if func + '(' in gen_content:
        count = gen_content.count(func + '(')
        print(f'{func}: CALLED {count}x')
    else:
        print(f'{func}: NOT CALLED!')

# =============================================
# CHECK 7: Render function - What's actually applied?
# =============================================
print('\n[7] RENDER FUNCTION ANALYSIS')
print('-' * 40)

render_start = gen_content.find('async def render_video')
render_end = gen_content.find('\nasync def', render_start + 10) if render_start > 0 else -1
if render_end < 0:
    render_end = gen_content.find('\ndef ', render_start + 10)

if render_start > 0 and render_end > 0:
    render_content = gen_content[render_start:render_end]
    
    # Check what's in render
    checks = [
        ('v12 text humanization', 'apply_v12_text_humanization'),
        ('AI font selection', 'font_choice'),
        ('Color grading', 'color_grad'),
        ('Dynamic SFX', 'random.*sfx'),
        ('Animation variety', 'animation_type'),
    ]
    
    for name, pattern in checks:
        if re.search(pattern, render_content, re.IGNORECASE):
            print(f'{name}: APPLIED')
        else:
            print(f'{name}: NOT APPLIED!')
else:
    print('render_video function: NOT FOUND!')

# =============================================
# CHECK 8: god_tier_prompts.py - What rules exist?
# =============================================
print('\n[8] GOD TIER PROMPTS CONTENT')
print('-' * 40)

try:
    with open('god_tier_prompts.py', 'r', encoding='utf-8') as f:
        prompts_content = f.read()
    
    # Check for key rules
    rules = [
        ('Numbered promise rule', 'NUMBERED PROMISE'),
        ('Believability rule', 'BELIEVABILITY'),
        ('Specific numbers', 'round number'),
        ('Quality minimum', 'minimum.*score'),
    ]
    
    for name, pattern in rules:
        if re.search(pattern, prompts_content, re.IGNORECASE):
            print(f'{name}: IN PROMPTS')
        else:
            print(f'{name}: NOT IN PROMPTS!')
            
except Exception as e:
    print(f'Could not read god_tier_prompts.py: {e}')

print('\n' + '=' * 80)
print('VERDICT: WHAT IS ACTUALLY BROKEN')
print('=' * 80)

issues = []

# Collect issues
if not ('font_choice' in gen_content or 'ai_font' in gen_content):
    issues.append('FONTS: Hardcoded, AI choice ignored')

if 'random.choice' not in gen_content or 'sfx' not in gen_content.lower():
    issues.append('SFX: Same effects every time, no variety')

if not found_rejection:
    issues.append('QUALITY: Low scores accepted, no minimum enforced')

if v12_master_ref < 3:
    issues.append('V12: Master prompt not properly injected')

for issue in issues:
    print(f'  [BROKEN] {issue}')

if not issues:
    print('  No obvious issues found - need deeper investigation')

print('\n' + '=' * 80)



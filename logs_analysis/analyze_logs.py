#!/usr/bin/env python3
import os
import re

logs_dir = '.'

# Define patterns to search for
patterns = {
    '429_errors': r'429|quota.*exhaust',
    'youtube_success': r'Upload complete.*Video ID|youtube\.com/shorts/',
    'video_generated': r'VIDEO GENERATED|Created:.*\.mp4',
    'quality_score': r'\[QUALITY\].*Score.*(\d+)/10',
    'phrases_count': r'Created (\d+) phrases|Phrases: (\d+)',
    'duration': r'Voiceover: ([\d.]+)s|duration=(\d+\.\d+)',
    'ai_module_errors': r'has no attribute|got an unexpected keyword',
    'rate_limit_active': r'cooldown|recovery in \d+s',
    'gemini_model': r'Gemini model: ([a-z0-9\-]+)',
    'groq_fallback': r'Using.*Groq.*fallback|Provider: groq',
}

results = {}
for log_file in os.listdir(logs_dir):
    if not log_file.startswith('run_') or not log_file.endswith('.txt'): continue
    run_id = log_file.replace('run_', '').replace('.txt', '')
    
    with open(os.path.join(logs_dir, log_file), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    results[run_id] = {
        '429_count': len(re.findall(patterns['429_errors'], content, re.I)),
        'youtube_ok': bool(re.search(patterns['youtube_success'], content)),
        'video_ok': bool(re.search(patterns['video_generated'], content)),
        'quality_scores': re.findall(r'\[QUALITY\].*Score.* (\d+)/10', content),
        'phrases': re.findall(r'Created (\d+) phrases', content),
        'durations': re.findall(r'Voiceover: ([\d.]+)s', content),
        'ai_module_errors': len(re.findall(patterns['ai_module_errors'], content)),
        'rate_limit_hits': len(re.findall(patterns['rate_limit_active'], content)),
        'gemini_models': re.findall(patterns['gemini_model'], content),
        'groq_uses': len(re.findall(r'Provider: groq', content)),
    }

print('='*80)
print('COMPREHENSIVE WORKFLOW ANALYSIS - 10 SCHEDULED RUNS')
print('='*80)
print()

for run_id, data in sorted(results.items(), key=lambda x: x[0], reverse=True):
    status = '[OK] SUCCESS' if data['youtube_ok'] else ('[?] NO UPLOAD' if data['video_ok'] else '[X] FAILED')
    quality = data['quality_scores'][0] if data['quality_scores'] else 'N/A'
    phrases = data['phrases'][0] if data['phrases'] else 'N/A'
    duration = data['durations'][0] if data['durations'] else 'N/A'
    gemini = data['gemini_models'][0] if data['gemini_models'] else 'N/A'
    print(f'Run {run_id}: {status}')
    print(f'  429 errors: {data["429_count"]} | Rate limit hits: {data["rate_limit_hits"]}')
    print(f'  Quality: {quality}/10 | Phrases: {phrases} | Duration: {duration}s')
    print(f'  Gemini Model: {gemini} | Groq calls: {data["groq_uses"]}')
    print(f'  AI Module Errors: {data["ai_module_errors"]}')
    print()

# Summary
total = len(results)
yt_success = sum(1 for r in results.values() if r['youtube_ok'])
vid_success = sum(1 for r in results.values() if r['video_ok'])
total_429 = sum(r['429_count'] for r in results.values())
total_ai_errors = sum(r['ai_module_errors'] for r in results.values())
total_rate_limits = sum(r['rate_limit_hits'] for r in results.values())

print('='*80)
print('SUMMARY')
print('='*80)
print(f'Total Runs: {total}')
print(f'YouTube Uploads: {yt_success}/{total} ({100*yt_success/total:.0f}%)')
print(f'Videos Generated: {vid_success}/{total} ({100*vid_success/total:.0f}%)')
print(f'Total 429 Errors: {total_429}')
print(f'Total Rate Limit Hits (recovery): {total_rate_limits}')
print(f'Total AI Module Errors: {total_ai_errors}')


#!/usr/bin/env python3
"""
Analyze codebase for prompts and hardcoded values.
"""

import re
import os
from pathlib import Path

def analyze():
    print("=" * 70)
    print("CODEBASE ANALYSIS: Prompts and Hardcoded Values")
    print("=" * 70)
    
    # Files to analyze
    py_files = list(Path('.').glob('*.py'))
    
    prompts = []
    hardcoded = []
    
    for filepath in py_files:
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            filename = filepath.name
            lines = content.split('\n')
            
            # Find AI prompts
            for i, line in enumerate(lines):
                if 'prompt' in line.lower() and ('"""' in line or "f'" in line or 'f"' in line):
                    # Get context
                    context = ' '.join(lines[i:i+3])[:100]
                    
                    # Determine type
                    nearby = ' '.join(lines[max(0,i-5):i+10]).lower()
                    if any(x in nearby for x in ['example:', 'like:', 'such as', 'base_categories']):
                        ptype = 'HYBRID'
                    else:
                        ptype = 'GENERIC'
                    
                    prompts.append({
                        'file': filename,
                        'line': i+1,
                        'type': ptype,
                        'context': context.replace('\n', ' ')[:80]
                    })
            
            # Find hardcoded values
            patterns = [
                (r'"llama-[^"]+"|\'llama-[^\']+\'', 'AI Model', 'Groq model name'),
                (r'"gemini-[^"]+"|\'gemini-[^\']+\'', 'AI Model', 'Gemini model name'),
                (r'"gpt-[^"]+"|\'gpt-[^\']+\'', 'AI Model', 'GPT model name'),
                (r'cron:\s*[\'"][0-9\s\*]+[\'"]', 'Schedule', 'Cron schedule'),
                (r'= 90000|= 100000|= 900000', 'Limit', 'Token/rate limit'),
            ]
            
            for pattern, category, desc in patterns:
                for match in re.finditer(pattern, content):
                    # Check if it's in a fallback context
                    start = max(0, match.start() - 150)
                    context = content[start:match.end()]
                    is_fallback = 'fallback' in context.lower() or 'except' in context.lower()
                    
                    hardcoded.append({
                        'file': filename,
                        'category': category,
                        'value': match.group()[:50],
                        'is_fallback': is_fallback,
                        'desc': desc
                    })
                    
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    # Print results
    print("\n" + "=" * 70)
    print("PROMPTS IN CODE")
    print("=" * 70)
    print(f"{'File':<30} {'Type':<10} {'Line':<6} Context")
    print("-" * 70)
    
    seen = set()
    for p in prompts:
        key = (p['file'], p['line'])
        if key not in seen:
            seen.add(key)
            # Safe print
            context = p['context'][:40].encode('ascii', 'ignore').decode('ascii')
            print(f"{p['file']:<30} {p['type']:<10} {p['line']:<6} {context}...")
    
    print(f"\nTotal prompts: {len(seen)}")
    
    print("\n" + "=" * 70)
    print("HARDCODED VALUES")
    print("=" * 70)
    print(f"{'File':<30} {'Category':<12} {'Fallback?':<10} Value")
    print("-" * 70)
    
    for h in hardcoded:
        fb = "Yes" if h['is_fallback'] else "NO"
        print(f"{h['file']:<30} {h['category']:<12} {fb:<10} {h['value']}")
    
    print(f"\nTotal hardcoded values: {len(hardcoded)}")
    print(f"  - In fallback context: {sum(1 for h in hardcoded if h['is_fallback'])}")
    print(f"  - NOT in fallback (may need review): {sum(1 for h in hardcoded if not h['is_fallback'])}")
    
    return prompts, hardcoded

if __name__ == "__main__":
    analyze()


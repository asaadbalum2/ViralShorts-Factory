"""
Find the last meaningful project-related prompts
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def find_meaningful_prompts():
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts_entry = [e for e in data if e.get('key') == 'aiService.prompts']
    prompts = prompts_entry[0]['data']
    
    # Look at the last 20 prompts to find meaningful ones
    print("Checking last 20 prompts for meaningful project-related content:\n")
    
    meaningful = []
    for i in range(len(prompts) - 1, max(0, len(prompts) - 21), -1):
        p = prompts[i]
        text = p.get('text', '') or p.get('textDescription', '') or str(p)
        
        # Skip recovery-related
        if any(kw in text.lower() for kw in ['recover', 'stuck', 'loading chat', 'rescue']):
            continue
        
        # Look for meaningful length and content
        if len(text.strip()) > 20:
            meaningful.append((i + 1, text[:500]))  # First 500 chars
            if len(meaningful) >= 5:
                break
    
    meaningful.reverse()
    
    print("=" * 80)
    print("LAST MEANINGFUL PROJECT PROMPTS:")
    print("=" * 80)
    
    for prompt_num, text in meaningful[-2:]:  # Last 2
        print(f"\n{'='*80}")
        print(f"PROMPT #{prompt_num}:")
        print(f"{'='*80}")
        print(text)
        if len(text) == 500:
            print("... [truncated]")
        print()

if __name__ == "__main__":
    find_meaningful_prompts()





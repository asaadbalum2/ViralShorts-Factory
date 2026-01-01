"""
Get the last 2 functional prompts about enhancements/integration
"""
import json
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def get_prompts():
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts_entry = [e for e in data if e.get('key') == 'aiService.prompts']
    prompts = prompts_entry[0]['data']
    
    gens_entry = [e for e in data if e.get('key') == 'aiService.generations']
    generations = gens_entry[0]['data'] if gens_entry else []
    
    # Find last prompts about enhancements/integration (not recovery)
    keywords = ['enhancement', 'integration', '419', 'integrated', 'v12', 'workflow', 'all of the']
    recovery_keywords = ['recover', 'stuck', 'loading chat', 'rescue', 'lost conversation']
    
    found = []
    for i in range(len(prompts) - 1, -1, -1):
        p = prompts[i]
        text = p.get('text', '') or p.get('textDescription', '') or str(p)
        text_lower = text.lower()
        
        # Skip recovery prompts
        if any(kw in text_lower for kw in recovery_keywords):
            continue
        
        # Look for meaningful project prompts
        if len(text.strip()) > 50 and any(kw in text_lower for kw in keywords):
            found.append((i + 1, text))
            if len(found) >= 2:
                break
    
    found.reverse()
    
    print("=" * 80)
    print("LAST 2 FUNCTIONAL PROMPTS (About Enhancements/Integration):")
    print("=" * 80)
    
    for prompt_num, text in found:
        print(f"\n{'='*80}")
        print(f"PROMPT #{prompt_num}:")
        print(f"{'='*80}")
        print(text)
        print()
    
    # Get last 2 responses
    if generations:
        print("=" * 80)
        print("LAST 2 RESPONSES:")
        print("=" * 80)
        
        for i, gen in enumerate(generations[-2:]):
            print(f"\n{'='*80}")
            print(f"RESPONSE #{len(generations) - 1 - i}:")
            print(f"{'='*80}")
            text = gen.get('textDescription', '') or gen.get('text', '') or str(gen)
            print(text[:4000] if len(text) > 4000 else text)
            if len(text) > 4000:
                print("\n... [truncated]")
            print()

if __name__ == "__main__":
    get_prompts()





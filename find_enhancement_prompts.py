"""
Find the last prompts about enhancements/integration
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def find_enhancement_prompts():
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts_entry = [e for e in data if e.get('key') == 'aiService.prompts']
    prompts = prompts_entry[0]['data']
    
    # Search for prompts about enhancements/integration
    keywords = ['enhancement', 'integration', '419', 'integrated', 'v12', 'workflow']
    
    found = []
    for i in range(len(prompts) - 1, -1, -1):
        p = prompts[i]
        text = p.get('text', '') or p.get('textDescription', '') or str(p)
        text_lower = text.lower()
        
        # Check if it contains relevant keywords
        if any(kw in text_lower for kw in keywords):
            # Skip if it's about chat recovery
            if not any(kw in text_lower for kw in ['recover', 'stuck', 'loading chat', 'rescue']):
                found.append((i + 1, text))
                if len(found) >= 3:
                    break
    
    found.reverse()
    
    print("=" * 80)
    print("LAST ENHANCEMENT/INTEGRATION PROMPTS:")
    print("=" * 80)
    
    for prompt_num, text in found[-2:]:  # Last 2
        print(f"\n{'='*80}")
        print(f"PROMPT #{prompt_num}:")
        print(f"{'='*80}")
            # Show first 2000 chars, handle encoding
            try:
                if len(text) > 2000:
                    print(text[:2000].encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
                    print("\n... [truncated, showing first 2000 chars]")
                else:
                    print(text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
            except:
                print(str(text)[:2000])
        print()
    
    # Get corresponding responses
    gens_entry = [e for e in data if e.get('key') == 'aiService.generations']
    if gens_entry:
        generations = gens_entry[0]['data']
        print("=" * 80)
        print("CORRESPONDING RESPONSES (Last 2):")
        print("=" * 80)
        
        for i, gen in enumerate(generations[-2:]):
            print(f"\n{'='*80}")
            print(f"RESPONSE #{len(generations) - 1 - i}:")
            print(f"{'='*80}")
            text = gen.get('textDescription', '') or gen.get('text', '') or str(gen)
            if len(text) > 3000:
                print(text[:3000])
                print("\n... [truncated]")
            else:
                print(text)
            print()

if __name__ == "__main__":
    find_enhancement_prompts()


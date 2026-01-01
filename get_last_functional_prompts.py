"""
Get the last 2 functional prompts before chat recovery
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def get_last_functional_prompts():
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get prompts
    prompts_entry = [e for e in data if e.get('key') == 'aiService.prompts']
    if not prompts_entry:
        print("No prompts found")
        return
    
    prompts = prompts_entry[0]['data']
    print(f"Total prompts: {len(prompts)}\n")
    
    # Get generations
    gens_entry = [e for e in data if e.get('key') == 'aiService.generations']
    generations = gens_entry[0]['data'] if gens_entry else []
    print(f"Total responses: {len(generations)}\n")
    
    # Find last functional prompts (not about chat recovery)
    recovery_keywords = ['recover', 'stuck', 'loading chat', 'rescue', 'lost conversation', 'chat']
    
    functional = []
    for i in range(len(prompts) - 1, -1, -1):
        p = prompts[i]
        text = p.get('text', '') or p.get('textDescription', '') or str(p)
        text_lower = text.lower()
        
        # Skip if it's about chat recovery
        if any(kw in text_lower for kw in recovery_keywords):
            continue
        
        # Skip very short prompts
        if len(text.strip()) < 10:
            continue
        
        functional.append((i + 1, text))
        if len(functional) >= 2:
            break
    
    functional.reverse()  # Show in order
    
    print("=" * 80)
    print("LAST 2 FUNCTIONAL PROMPTS (Before Chat Recovery)")
    print("=" * 80)
    
    for prompt_num, text in functional:
        print(f"\n{'='*80}")
        print(f"PROMPT #{prompt_num}:")
        print(f"{'='*80}")
        print(text)
        print()
    
    # Try to find corresponding responses
    print("=" * 80)
    print("CORRESPONDING RESPONSES:")
    print("=" * 80)
    print("\nNote: There are fewer responses than prompts.")
    print("Showing last 2 responses from the conversation:\n")
    
    for i, gen in enumerate(generations[-2:]):
        print(f"{'='*80}")
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
    get_last_functional_prompts()





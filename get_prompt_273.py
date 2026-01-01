"""
Get prompt #273
"""
import json
from pathlib import Path
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def get_prompt_273():
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts_entry = [e for e in data if e.get('key') == 'aiService.prompts']
    prompts = prompts_entry[0]['data']
    
    if len(prompts) >= 273:
        prompt_273 = prompts[272]  # 0-indexed
        text = prompt_273.get('text', '') or prompt_273.get('textDescription', '') or str(prompt_273)
        
        print("=" * 80)
        print("PROMPT #273:")
        print("=" * 80)
        print(text)
        print()
        
        # Also show context - prompts before and after
        print("=" * 80)
        print("CONTEXT (Prompts around #273):")
        print("=" * 80)
        
        for i in range(max(0, 270), min(len(prompts), 276)):
            p = prompts[i]
            text = p.get('text', '') or p.get('textDescription', '') or str(p)
            print(f"\n--- PROMPT #{i+1} ---")
            print(text[:500] if len(text) > 500 else text)
            if len(text) > 500:
                print("... [truncated]")
    else:
        print(f"Only {len(prompts)} prompts found, cannot get prompt #273")

if __name__ == "__main__":
    get_prompt_273()





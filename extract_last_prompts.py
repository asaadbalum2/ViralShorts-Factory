"""
Extract the last 2 prompts (278 and 279) and their responses
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def extract_last_prompts():
    """Extract last 2 prompts and responses"""
    if not RECOVERED_CHAT_FILE.exists():
        print("[ERROR] recovered_chat_complete.json not found")
        return
    
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    prompts_data = []
    generations_data = []
    
    for entry in recovered_data:
        key = entry.get('key')
        data = entry.get('data')
        
        if key == 'aiService.prompts' and isinstance(data, list):
            prompts_data = data
        elif key == 'aiService.generations' and isinstance(data, list):
            generations_data = data
    
    print("=" * 60)
    print("LAST 2 PROMPTS (278 and 279)")
    print("=" * 60)
    
    if len(prompts_data) >= 2:
        # Get last 2 prompts
        prompt_278 = prompts_data[-2]
        prompt_279 = prompts_data[-1]
        
        print("\n" + "=" * 60)
        print("PROMPT #278:")
        print("=" * 60)
        if isinstance(prompt_278, dict):
            text = prompt_278.get('textDescription') or prompt_278.get('text') or str(prompt_278)
            print(text)
        else:
            print(str(prompt_278))
        
        print("\n" + "=" * 60)
        print("PROMPT #279:")
        print("=" * 60)
        if isinstance(prompt_279, dict):
            text = prompt_279.get('textDescription') or prompt_279.get('text') or str(prompt_279)
            print(text)
        else:
            print(str(prompt_279))
    
    # Find corresponding responses
    if len(generations_data) >= 2:
        # Get last 2 responses
        response_278 = generations_data[-2] if len(generations_data) >= 2 else None
        response_279 = generations_data[-1] if len(generations_data) >= 1 else None
        
        if response_278:
            print("\n" + "=" * 60)
            print("RESPONSE TO PROMPT #278:")
            print("=" * 60)
            if isinstance(response_278, dict):
                text = response_278.get('textDescription') or response_278.get('text') or str(response_278)
                print(text[:2000] + "..." if len(text) > 2000 else text)
            else:
                print(str(response_278)[:2000] + "..." if len(str(response_278)) > 2000 else str(response_278))
        
        if response_279:
            print("\n" + "=" * 60)
            print("RESPONSE TO PROMPT #279:")
            print("=" * 60)
            if isinstance(response_279, dict):
                text = response_279.get('textDescription') or response_279.get('text') or str(response_279)
                print(text[:2000] + "..." if len(text) > 2000 else text)
            else:
                print(str(response_279)[:2000] + "..." if len(str(response_279)) > 2000 else str(response_279))
    
    print("\n" + "=" * 60)
    print(f"Total prompts: {len(prompts_data)}")
    print(f"Total responses: {len(generations_data)}")
    print("=" * 60)

if __name__ == "__main__":
    extract_last_prompts()





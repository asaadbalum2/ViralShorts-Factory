"""
Extract the last functional prompts (before chat recovery attempts)
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def extract_last_functional_prompts():
    """Extract last functional prompts before chat recovery"""
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
    print("LAST FUNCTIONAL PROMPTS (Before Chat Recovery)")
    print("=" * 60)
    
    # Find the last prompts that are NOT about chat recovery
    # Chat recovery prompts contain: "recover", "stuck", "chat", "loading"
    recovery_keywords = ['recover', 'stuck', 'loading chat', 'chat', 'rescue', 'lost conversation']
    
    functional_prompts = []
    for i, prompt in enumerate(reversed(prompts_data)):
        if isinstance(prompt, dict):
            text = prompt.get('text') or prompt.get('textDescription') or str(prompt)
        else:
            text = str(prompt)
        
        # Check if it's a recovery-related prompt
        is_recovery = any(keyword in text.lower() for keyword in recovery_keywords)
        
        if not is_recovery and len(text.strip()) > 10:  # Ignore very short prompts
            functional_prompts.append((len(prompts_data) - i, prompt, text))
            if len(functional_prompts) >= 5:  # Get last 5 functional prompts
                break
    
    # Reverse to show in chronological order
    functional_prompts.reverse()
    
    print(f"\nFound {len(functional_prompts)} last functional prompts:\n")
    
    for prompt_num, prompt_obj, text in functional_prompts[-2:]:  # Show last 2
        print("=" * 60)
        print(f"PROMPT #{prompt_num}:")
        print("=" * 60)
        print(text)
        print()
    
    # Find corresponding responses
    print("=" * 60)
    print("CORRESPONDING RESPONSES:")
    print("=" * 60)
    
    # Get the generation that corresponds to these prompts
    # Note: There are 50 generations for 279 prompts, so not all prompts have responses
    # We need to find which generation corresponds to which prompt
    
    if functional_prompts:
        # Show responses if available
        last_prompt_num = functional_prompts[-1][0]
        print(f"\nNote: There are {len(generations_data)} responses for {len(prompts_data)} prompts")
        print("The responses may not directly correspond to prompt numbers")
        print("Showing last 2 responses from the conversation:")
        print()
        
        for i, gen in enumerate(generations_data[-2:]):
            print("=" * 60)
            print(f"RESPONSE #{len(generations_data) - 1 - i}:")
            print("=" * 60)
            if isinstance(gen, dict):
                text = gen.get('textDescription') or gen.get('text') or str(gen)
                # Show first 2000 chars
                if len(text) > 2000:
                    print(text[:2000])
                    print("\n... [truncated, full response is longer]")
                else:
                    print(text)
            else:
                text = str(gen)
                if len(text) > 2000:
                    print(text[:2000])
                    print("\n... [truncated, full response is longer]")
                else:
                    print(text)
            print()
    
    print("=" * 60)
    print(f"Total prompts: {len(prompts_data)}")
    print(f"Total responses: {len(generations_data)}")
    print("=" * 60)

if __name__ == "__main__":
    extract_last_functional_prompts()





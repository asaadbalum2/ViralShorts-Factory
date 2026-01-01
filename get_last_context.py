"""
Get the last few messages so you can continue the conversation
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def get_last_context():
    """Get the last few messages for continuation"""
    if not RECOVERED_CHAT_FILE.exists():
        print("[ERROR] recovered_chat_complete.json not found")
        return
    
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    prompts = []
    generations = []
    
    for entry in recovered_data:
        key = entry.get('key')
        data = entry.get('data')
        
        if key == 'aiService.prompts' and isinstance(data, list):
            prompts = data
        elif key == 'aiService.generations' and isinstance(data, list):
            generations = data
    
    print("=" * 60)
    print("LAST 5 MESSAGES - To Continue Your Project")
    print("=" * 60)
    
    # Get last 5 prompts and responses
    last_prompts = prompts[-5:] if len(prompts) > 5 else prompts
    last_generations = generations[-5:] if len(generations) > 5 else generations
    
    print("\nLast conversation context:\n")
    
    for i, (prompt, gen) in enumerate(zip(last_prompts, last_generations), 1):
        prompt_text = prompt.get('text', '') if isinstance(prompt, dict) else str(prompt)
        gen_text = gen.get('textDescription', '') if isinstance(gen, dict) else str(gen)
        
        print(f"\n--- Message {len(prompts) - len(last_prompts) + i} ---")
        print(f"\nYOU: {prompt_text[:200]}...")
        print(f"\nAI: {gen_text[:200]}...")
    
    print("\n" + "=" * 60)
    print("To continue:")
    print("=" * 60)
    print("\n1. If Cursor opens the chat - just continue typing!")
    print("2. If Cursor won't open it - create a NEW chat and paste:")
    print("   'Continuing from previous conversation about [your project]'")
    print("   Then continue with your next question/request")
    print("\nYour full conversation history is in:")
    print("  - chat_viewer.html (all messages)")
    print("  - recovered_chat_readable.txt (text format)")
    print("=" * 60)

if __name__ == "__main__":
    get_last_context()
















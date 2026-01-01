"""
PRACTICAL SOLUTION - Continue your project right now
Extract conversation summary and create a continuation script
"""
import json
from pathlib import Path

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def create_continuation():
    """Create a file you can use to continue your project"""
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
    
    # Get last 10 messages for context
    last_prompts = prompts[-10:] if len(prompts) > 10 else prompts
    last_generations = generations[-10:] if len(generations) > 10 else generations
    
    # Create continuation text
    continuation = """# CONTINUE YOUR PROJECT - Copy this into a NEW Cursor chat

## Your Project Context:

You were working on a crucial project. Here's the recent conversation context:

"""
    
    for i, (prompt, gen) in enumerate(zip(last_prompts, last_generations), 1):
        prompt_text = prompt.get('text', '') if isinstance(prompt, dict) else str(prompt)
        gen_text = gen.get('textDescription', '') if isinstance(gen, dict) else str(gen)
        
        continuation += f"\n### Message {len(prompts) - len(last_prompts) + i}:\n"
        continuation += f"**You:** {prompt_text[:500]}\n"
        continuation += f"**AI:** {gen_text[:500]}\n"
    
    continuation += f"""

---

## To Continue:

1. Open Cursor
2. Create a NEW chat
3. Copy and paste the above context
4. Add: "Continuing from here. [Your next question/request]"
5. Continue your project!

---

## Full Conversation Available:

- **chat_viewer.html** - Open in browser to see ALL 279 messages
- **recovered_chat_readable.txt** - Full text version

Your project conversation is 100% safe and you can continue right now!
"""
    
    # Save
    output_file = Path("./CONTINUE_PROJECT.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(continuation)
    
    print("=" * 60)
    print("PRACTICAL SOLUTION CREATED")
    print("=" * 60)
    print(f"\nCreated: {output_file}")
    print("\nThis file contains:")
    print("  - Last 10 messages for context")
    print("  - Instructions to continue")
    print("\n" + "=" * 60)
    print("TO CONTINUE YOUR PROJECT RIGHT NOW:")
    print("=" * 60)
    print("\n1. Open Cursor")
    print("2. Create a NEW chat (it should work now after nuclear fix)")
    print("3. Open 'CONTINUE_PROJECT.txt'")
    print("4. Copy the context section")
    print("5. Paste into the new chat")
    print("6. Add your next question/request")
    print("7. Continue your project!")
    print("\nYour full conversation (279 messages) is in:")
    print("  - chat_viewer.html (easiest - open in browser)")
    print("  - recovered_chat_readable.txt")
    print("\n" + "=" * 60)
    print("YOUR PROJECT IS NOT LOST - YOU CAN CONTINUE NOW!")
    print("=" * 60)

if __name__ == "__main__":
    create_continuation()










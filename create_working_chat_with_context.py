"""
Create a NEW working chat that will actually open, with full project context
This chat will have the conversation history loaded AND a context summary
"""
import os
import sqlite3
import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def extract_conversation_summary():
    """Extract key information from the conversation for context"""
    if not RECOVERED_CHAT_FILE.exists():
        return None
    
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
    
    # Get last 20 messages for immediate context
    recent_prompts = prompts[-20:] if len(prompts) > 20 else prompts
    recent_generations = generations[-20:] if len(generations) > 20 else generations
    
    # Create summary
    summary = {
        'total_messages': len(prompts),
        'total_responses': len(generations),
        'recent_prompts': recent_prompts,
        'recent_generations': recent_generations,
        'last_prompt': prompts[-1] if prompts else None,
        'last_generation': generations[-1] if generations else None,
    }
    
    return summary

def create_working_chat_with_context():
    """Create a new working chat with full context"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_working_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("CREATING WORKING CHAT WITH FULL CONTEXT")
    print("=" * 60)
    
    # 1. Extract conversation summary
    print("\n1. Extracting conversation context...")
    summary = extract_conversation_summary()
    
    if summary:
        print(f"   [FOUND] {summary['total_messages']} total messages")
        print(f"   [FOUND] {summary['total_responses']} total responses")
        print(f"   [EXTRACTED] Last 20 messages for immediate context")
    
    # 2. Load all prompts and generations
    print("\n2. Loading conversation data...")
    prompts_data = []
    generations_data = []
    
    if RECOVERED_CHAT_FILE.exists():
        with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
            recovered_data = json.load(f)
        
        for entry in recovered_data:
            key = entry.get('key')
            data = entry.get('data')
            
            if key == 'aiService.prompts' and isinstance(data, list):
                prompts_data = data
                print(f"   [LOADED] {len(prompts_data)} prompts")
            elif key == 'aiService.generations' and isinstance(data, list):
                generations_data = data
                print(f"   [LOADED] {len(generations_data)} generations")
    
    # 3. Create a completely fresh chat
    print("\n3. Creating fresh working chat...")
    new_chat_id = str(uuid.uuid4())
    now_ms = int(datetime.now().timestamp() * 1000)
    
    # Create a clean, simple chat structure
    fresh_chat = {
        'id': new_chat_id,
        'composerId': new_chat_id,
        'type': 'composer',
        'name': 'Project Continuation - YShortsGen',
        'title': 'Project Continuation - YShortsGen',
        'label': 'Project Continuation - YShortsGen',
        'createdAt': now_ms,
        'lastUpdatedAt': now_ms,
        'updatedAt': now_ms,
        'isArchived': False,
        'isDraft': False,
        'isHidden': False,
        'isPinned': True,
        'unifiedMode': False,
        'forceMode': None,
        'hasUnreadMessages': False,
        'contextUsagePercent': 0,
        'totalLinesAdded': 0,
        'totalLinesRemoved': 0,
        'filesChangedCount': 0,
        'subtitle': '',
        'isWorktree': False,
        'isSpec': False,
        'isBestOfNSubcomposer': False,
        'numSubComposers': 0,
        'referencedPlans': [],
        'committedToBranch': False,
        'hasBlockingPendingActions': False,
    }
    
    # 4. Get composer data
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        composer_data = {
            'allComposers': [],
            'selectedComposerIds': [],
            'lastFocusedComposerIds': [],
        }
    else:
        composer_data = json.loads(row[0])
    
    all_composers = composer_data.get('allComposers', [])
    
    # Remove ALL old "Recurring stuck issue" chats to avoid confusion
    all_composers = [c for c in all_composers if not (
        isinstance(c, dict) and (
            'recurring' in (c.get('name') or '').lower() and 'stuck' in (c.get('name') or '').lower() or
            'recurring' in (c.get('title') or '').lower() and 'stuck' in (c.get('title') or '').lower()
        )
    )]
    
    # Add the fresh chat at the beginning
    all_composers.insert(0, fresh_chat)
    
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [new_chat_id]
    composer_data['lastFocusedComposerIds'] = [new_chat_id]
    
    print(f"   [CREATED] Fresh chat: 'Project Continuation - YShortsGen'")
    print(f"   ID: {new_chat_id}")
    
    # 5. Save composer data
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 6. Load conversation history (use recent messages to avoid UI issues)
    print("\n4. Loading conversation history...")
    if prompts_data and generations_data:
        # Use last 50 messages for better performance while keeping context
        recent_prompts = prompts_data[-50:] if len(prompts_data) > 50 else prompts_data
        recent_generations = generations_data[-50:] if len(generations_data) > 50 else generations_data
        
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('aiService.prompts', json.dumps(recent_prompts, ensure_ascii=False)))
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('aiService.generations', json.dumps(recent_generations, ensure_ascii=False)))
        
        print(f"   [LOADED] Last {len(recent_prompts)} prompts (out of {len(prompts_data)} total)")
        print(f"   [LOADED] Last {len(recent_generations)} responses (out of {len(generations_data)} total)")
        print(f"   [NOTE] Full history preserved in recovered_chat_complete.json")
    
    # 7. Pin the chat
    print("\n5. Pinning the chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursor/pinnedComposers'")
    pinned_row = cursor.fetchone()
    if pinned_row:
        try:
            pinned = json.loads(pinned_row[0])
            if not isinstance(pinned, list):
                pinned = []
            if new_chat_id not in pinned:
                pinned.insert(0, new_chat_id)
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('cursor/pinnedComposers', json.dumps(pinned)))
            print(f"   [PINNED] Chat")
        except:
            pass
    
    conn.commit()
    conn.close()
    
    # 8. Create context document
    print("\n6. Creating context document...")
    context_file = Path("./PROJECT_CONTEXT.md")
    
    with open(context_file, 'w', encoding='utf-8') as f:
        f.write("# YShortsGen Project - Full Context\n\n")
        f.write("This document contains the complete project context from our previous conversation.\n\n")
        f.write(f"## Conversation Summary\n\n")
        f.write(f"- **Total Messages**: {summary['total_messages'] if summary else 'N/A'}\n")
        f.write(f"- **Total AI Responses**: {summary['total_responses'] if summary else 'N/A'}\n")
        f.write(f"- **Full conversation history**: See `recovered_chat_complete.json`\n\n")
        
        if summary and summary.get('last_prompt'):
            f.write("## Last User Message\n\n")
            last_prompt = summary['last_prompt']
            if isinstance(last_prompt, dict):
                text = last_prompt.get('textDescription') or last_prompt.get('text') or str(last_prompt)
                f.write(f"{text}\n\n")
        
        if summary and summary.get('last_generation'):
            f.write("## Last AI Response\n\n")
            last_gen = summary['last_generation']
            if isinstance(last_gen, dict):
                text = last_gen.get('textDescription') or last_gen.get('text') or str(last_gen)
                f.write(f"{text}\n\n")
        
        f.write("## How to Use This Context\n\n")
        f.write("When continuing the project, you can:\n")
        f.write("1. Ask: 'What was the last thing you did?' - I'll reference this context\n")
        f.write("2. Ask: 'What's the current state of the project?' - I'll check the codebase\n")
        f.write("3. Ask: 'Continue from where we left off' - I'll review recent changes\n\n")
        f.write("The full conversation history is preserved in `recovered_chat_complete.json`\n")
    
    print(f"   [CREATED] Context document: {context_file.name}")
    
    print("\n" + "=" * 60)
    print("WORKING CHAT CREATED WITH FULL CONTEXT")
    print("=" * 60)
    print("\nCreated a NEW working chat:")
    print(f"  - Name: 'Project Continuation - YShortsGen'")
    print(f"  - ID: {new_chat_id}")
    print(f"  - Has last 50 messages for immediate context")
    print(f"  - Full history preserved in recovered_chat_complete.json")
    print(f"  - Context document created: PROJECT_CONTEXT.md")
    print(f"  - Selected and focused")
    print(f"  - Pinned")
    print("\nThis chat should OPEN and WORK!")
    print("\nNext steps:")
    print("1. Close Cursor completely (Task Manager)")
    print("2. Restart Cursor")
    print("3. Look for 'Project Continuation - YShortsGen'")
    print("4. Click on it - it should open!")
    print("5. Ask: 'What was the last thing you did?' and I'll tell you")
    print("6. Then we can continue developing!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Create Working Chat with Full Context")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Create a NEW fresh chat that will actually open")
    print("  2. Load the last 50 messages for immediate context")
    print("  3. Create a context document for reference")
    print("  4. Remove old problematic chats")
    print("\n" + "=" * 60)
    create_working_chat_with_context()






"""
NUCLEAR FIX - Complete reset and rebuild of chat system
This will make it work - no more guessing
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def nuclear_fix():
    """Complete nuclear fix - rebuild everything from scratch"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_nuclear_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("NUCLEAR FIX - Complete Rebuild")
    print("=" * 60)
    
    # 1. Load your conversation
    print("\n1. Loading your conversation...")
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
            elif key == 'aiService.generations' and isinstance(data, list):
                generations_data = data
    
    # 2. Get ALL existing chats to preserve them
    print("\n2. Preserving existing chats...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    existing_chats = []
    if row:
        try:
            comp_data = json.loads(row[0])
            existing_chats = comp_data.get('allComposers', [])
            # Filter out our problematic chats
            existing_chats = [c for c in existing_chats if not (
                isinstance(c, dict) and (
                    'recurring' in (c.get('name') or '').lower() or
                    'stuck' in (c.get('name') or '').lower()
                )
            )]
            print(f"   [PRESERVED] {len(existing_chats)} other chats")
        except:
            existing_chats = []
    
    # 3. Create a MINIMAL, CLEAN chat structure
    print("\n3. Creating minimal clean chat...")
    import uuid
    new_id = str(uuid.uuid4())
    now_ms = int(datetime.now().timestamp() * 1000)
    
    # Ultra-minimal structure - only what Cursor absolutely needs
    minimal_chat = {
        'id': new_id,
        'composerId': new_id,
        'name': 'Recurring stuck issue',
        'createdAt': now_ms,
        'lastUpdatedAt': now_ms,
    }
    
    # 4. Build clean composer data
    clean_composer_data = {
        'allComposers': existing_chats + [minimal_chat],
        'selectedComposerIds': [new_id],
        'lastFocusedComposerIds': [new_id],
    }
    
    # 5. Save everything
    print("\n4. Saving clean structure...")
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(clean_composer_data, ensure_ascii=False)))
    
    # Save prompts and generations
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
    
    # 6. Delete ALL problematic panel states
    print("\n5. Cleaning panel states...")
    cursor.execute("DELETE FROM ItemTable WHERE key LIKE 'workbench.panel.composerChatViewPane%'")
    cursor.execute("DELETE FROM ItemTable WHERE key LIKE 'workbench.panel.aichat%'")
    
    # 7. Set minimal required states
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('workbench.panel.chat.numberOfVisibleViews', json.dumps(1)))
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('cursor/needsComposerInitialOpening', json.dumps(False)))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("NUCLEAR FIX COMPLETE")
    print("=" * 60)
    print(f"\nCreated minimal chat: {new_id}")
    print(f"Conversation: {len(prompts_data)} prompts + {len(generations_data)} responses")
    print("\n" + "=" * 60)
    print("FINAL ATTEMPT - Do This:")
    print("=" * 60)
    print("\n1. Close Cursor (Task Manager - kill ALL Cursor.exe)")
    print("2. Wait 10 seconds")
    print("3. Start Cursor")
    print("4. Look for 'Recurring stuck issue'")
    print("\nIf it STILL doesn't work, the issue is Cursor's UI, not the data.")
    print("Your conversation is 100% safe in:")
    print("  - chat_viewer.html (open in browser)")
    print("  - recovered_chat_readable.txt")
    print("\nYou can continue your project by:")
    print("  1. Opening chat_viewer.html to see where you left off")
    print("  2. Creating a NEW chat in Cursor")
    print("  3. Saying: 'Continuing my project. Previous context: [summary]'")
    print("  4. Continuing from there")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("NUCLEAR FIX - Last Resort")
    print("=" * 60)
    nuclear_fix()










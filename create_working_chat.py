"""
Create a working chat that Cursor will actually open and link your conversation
"""
import os
import sqlite3
import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def create_working_chat():
    """Create a fresh working chat and ensure it opens"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_working_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("CREATING WORKING CHAT FOR CONTINUATION")
    print("=" * 60)
    
    # 1. Load your conversation data
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
                print(f"   [LOADED] {len(prompts_data)} prompts")
            elif key == 'aiService.generations' and isinstance(data, list):
                generations_data = data
                print(f"   [LOADED] {len(generations_data)} generations")
    
    # 2. Create a completely fresh chat with a simple name
    print("\n2. Creating fresh working chat...")
    new_chat_id = str(uuid.uuid4())
    now_ms = int(datetime.now().timestamp() * 1000)
    
    # Create a simple, clean chat structure
    fresh_chat = {
        'id': new_chat_id,
        'composerId': new_chat_id,
        'type': 'composer',
        'name': 'Recurring stuck issue',
        'title': 'Recurring stuck issue',
        'createdAt': now_ms,
        'lastUpdatedAt': now_ms,
        'updatedAt': now_ms,
        'isArchived': False,
        'isDraft': False,
        'isHidden': False,
        'isPinned': False,  # Don't pin - let it appear naturally
        'unifiedMode': False,
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
    
    # 3. Get composer data
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        composer_data = {
            'allComposers': [],
            'selectedComposerIds': [],
            'lastFocusedComposerIds': [],
            'hasMigratedComposerData': True,
            'hasMigratedMultipleComposers': True
        }
    else:
        composer_data = json.loads(row[0])
    
    all_composers = composer_data.get('allComposers', [])
    
    # Remove any old "Recurring stuck issue" to avoid confusion
    all_composers = [c for c in all_composers if not (
        isinstance(c, dict) and (
            (c.get('name') or '').lower() == 'recurring stuck issue' or
            (c.get('title') or '').lower() == 'recurring stuck issue'
        )
    )]
    
    # Add the fresh chat at the beginning
    all_composers.insert(0, fresh_chat)
    
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [new_chat_id]
    composer_data['lastFocusedComposerIds'] = [new_chat_id]
    
    # Save
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 4. Save prompts and generations - these are the conversation history
    print("\n3. Saving conversation history...")
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
    print(f"   [SAVED] All {len(prompts_data)} prompts and {len(generations_data)} responses")
    
    # 5. Create minimal panel state
    print("\n4. Setting up minimal UI state...")
    panel_id = str(uuid.uuid4())
    view_key = f"workbench.panel.aichat.view.{new_chat_id}"
    panel_key = f"workbench.panel.composerChatViewPane.{panel_id}"
    
    panel_data = {
        view_key: {
            'collapsed': False,
            'isHidden': False
        }
    }
    
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (panel_key, json.dumps(panel_data)))
    
    # 6. Ensure chat panel is visible
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('workbench.panel.chat.numberOfVisibleViews', json.dumps(1)))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("WORKING CHAT CREATED")
    print("=" * 60)
    print(f"\nNew chat ID: {new_chat_id}")
    print(f"Name: 'Recurring stuck issue'")
    print(f"Conversation: {len(prompts_data)} prompts + {len(generations_data)} responses")
    print("\n" + "=" * 60)
    print("CRITICAL STEPS TO CONTINUE YOUR PROJECT:")
    print("=" * 60)
    print("\n1. Close Cursor completely (Task Manager - end all Cursor.exe)")
    print("2. Wait 5 seconds")
    print("3. Start Cursor")
    print("4. The chat 'Recurring stuck issue' should appear")
    print("5. Click on it - it should open with ALL your conversation")
    print("6. You can continue your project from where you left off!")
    print("\nIf it still doesn't open, try:")
    print("  - Look for chat icon in sidebar")
    print("  - Check bottom panel for chat tab")
    print("  - The chat should be in the main list (not archived)")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Create Working Chat - Continue Your Project")
    print("=" * 60)
    create_working_chat()
















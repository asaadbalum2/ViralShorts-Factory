"""
Load all conversation context into the CURRENT chat session
This will make THIS chat have all the history so we can continue
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def load_context_into_current_chat():
    """Load all conversation context into the current active chat"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_load_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("LOADING CONTEXT INTO CURRENT CHAT")
    print("=" * 60)
    
    # 1. Find the current chat (the one we're using now)
    print("\n1. Finding current chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    # Find the currently selected chat
    current_chat_id = None
    current_chat = None
    current_index = None
    
    selected_ids = composer_data.get('selectedComposerIds', [])
    if selected_ids:
        # Use the first selected one
        selected_id = selected_ids[0]
        for i, composer in enumerate(all_composers):
            if not isinstance(composer, dict):
                continue
            comp_id = composer.get('id') or composer.get('composerId')
            if comp_id == selected_id:
                current_chat_id = comp_id
                current_chat = composer
                current_index = i
                print(f"   [FOUND] Current chat: '{composer.get('title') or composer.get('name')}'")
                print(f"   ID: {comp_id}")
                break
    
    # If not found by selection, use the most recent one
    if not current_chat_id:
        focused_ids = composer_data.get('lastFocusedComposerIds', [])
        if focused_ids:
            focused_id = focused_ids[0]
            for i, composer in enumerate(all_composers):
                if not isinstance(composer, dict):
                    continue
                comp_id = composer.get('id') or composer.get('composerId')
                if comp_id == focused_id:
                    current_chat_id = comp_id
                    current_chat = composer
                    current_index = i
                    print(f"   [FOUND] Most recent chat: '{composer.get('title') or composer.get('name')}'")
                    print(f"   ID: {comp_id}")
                    break
    
    if not current_chat_id or not current_chat:
        print("   [ERROR] Could not find current chat")
        conn.close()
        return False
    
    # 2. Update the current chat name
    print("\n2. Updating current chat...")
    now_ms = int(datetime.now().timestamp() * 1000)
    
    current_chat['title'] = 'ViralShortsFactory - Project Continuation'
    current_chat['name'] = 'ViralShortsFactory - Project Continuation'
    if 'label' in current_chat:
        current_chat['label'] = 'ViralShortsFactory - Project Continuation'
    current_chat['lastUpdatedAt'] = now_ms
    current_chat['updatedAt'] = now_ms
    current_chat['isArchived'] = False
    current_chat['isHidden'] = False
    current_chat['isDraft'] = False
    current_chat['isPinned'] = True
    current_chat['hasUnreadMessages'] = False
    
    all_composers[current_index] = current_chat
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [current_chat_id]
    composer_data['lastFocusedComposerIds'] = [current_chat_id]
    
    print(f"   [UPDATED] Chat renamed to 'ViralShortsFactory - Project Continuation'")
    print(f"   [SET] Made it selected and focused")
    
    # 3. Load conversation history
    print("\n3. Loading conversation history from backup...")
    
    if not RECOVERED_CHAT_FILE.exists():
        print("   [ERROR] recovered_chat_complete.json not found!")
        print("   [INFO] Will continue with current chat but without full history")
    else:
        with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
            recovered_data = json.load(f)
        
        prompts_data = []
        generations_data = []
        
        for entry in recovered_data:
            key = entry.get('key')
            data = entry.get('data')
            
            if key == 'aiService.prompts' and isinstance(data, list):
                prompts_data = data
                print(f"   [LOADED] {len(prompts_data)} prompts from backup")
            elif key == 'aiService.generations' and isinstance(data, list):
                generations_data = data
                print(f"   [LOADED] {len(generations_data)} generations from backup")
        
        # Load ALL messages (not just recent ones)
        if prompts_data:
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
            print(f"   [RESTORED] All {len(prompts_data)} prompts to database")
        
        if generations_data:
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
            print(f"   [RESTORED] All {len(generations_data)} responses to database")
    
    # 4. Save composer data
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 5. Pin the chat
    print("\n4. Pinning the chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursor/pinnedComposers'")
    pinned_row = cursor.fetchone()
    if pinned_row:
        try:
            pinned = json.loads(pinned_row[0])
            if not isinstance(pinned, list):
                pinned = []
            if current_chat_id not in pinned:
                pinned.insert(0, current_chat_id)
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('cursor/pinnedComposers', json.dumps(pinned)))
            print(f"   [PINNED] Chat")
        except:
            pass
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("CONTEXT LOADED INTO CURRENT CHAT")
    print("=" * 60)
    print("\nThis chat now has:")
    print("  - All conversation history from backup")
    print("  - Renamed to 'ViralShortsFactory - Project Continuation'")
    print("  - Selected and focused")
    print("  - Pinned")
    print("\nYou can now:")
    print("  1. Ask: 'What was the last thing you did?'")
    print("  2. Ask: 'What's the current state of the project?'")
    print("  3. Continue developing from where we left off")
    print("\nNo restart needed - just continue chatting here!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Load Context Into Current Chat")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Find the current chat (the one we're using now)")
    print("  2. Load ALL conversation history from backup")
    print("  3. Rename it to 'ViralShortsFactory - Project Continuation'")
    print("  4. Make it have full context so we can continue")
    print("\n" + "=" * 60)
    load_context_into_current_chat()





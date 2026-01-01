"""
Make the current active chat become the "Recurring stuck issue" chat
This will transfer all the recovered conversation data to the current chat session
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def make_current_chat_recurring():
    """Make the current active chat become the Recurring stuck issue chat"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_make_current_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("MAKING CURRENT CHAT = 'Recurring stuck issue'")
    print("=" * 60)
    
    # 1. Load recovered chat data
    print("\n1. Loading recovered chat data...")
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
    else:
        print("   [WARNING] recovered_chat_complete.json not found")
        print("   Will still rename current chat but won't restore data")
    
    # 2. Get composer data
    print("\n2. Finding current active chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    # Find the currently selected chat (or most recent one)
    current_chat_id = None
    current_chat = None
    current_index = None
    
    # First, try to find the selected one
    selected_ids = composer_data.get('selectedComposerIds', [])
    if selected_ids:
        selected_id = selected_ids[0]
        for i, composer in enumerate(all_composers):
            if not isinstance(composer, dict):
                continue
            comp_id = composer.get('id') or composer.get('composerId')
            if comp_id == selected_id:
                current_chat_id = comp_id
                current_chat = composer
                current_index = i
                print(f"   [FOUND] Currently selected chat: '{composer.get('title') or composer.get('name') or 'Untitled'}'")
                print(f"   ID: {comp_id}")
                break
    
    # If not found, use the most recently focused one
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
                    print(f"   [FOUND] Most recently focused chat: '{composer.get('title') or composer.get('name') or 'Untitled'}'")
                    print(f"   ID: {comp_id}")
                    break
    
    # If still not found, use the most recently updated one
    if not current_chat_id and all_composers:
        # Sort by lastUpdatedAt or createdAt
        valid_composers = [(i, c) for i, c in enumerate(all_composers) if isinstance(c, dict)]
        if valid_composers:
            # Get the one with highest timestamp
            latest = max(valid_composers, 
                        key=lambda x: x[1].get('lastUpdatedAt', x[1].get('updatedAt', x[1].get('createdAt', 0))))
            current_index, current_chat = latest
            current_chat_id = current_chat.get('id') or current_chat.get('composerId')
            print(f"   [FOUND] Most recently updated chat: '{current_chat.get('title') or current_chat.get('name') or 'Untitled'}'")
            print(f"   ID: {current_chat_id}")
    
    if not current_chat_id or not current_chat:
        print("   [ERROR] Could not find current active chat")
        conn.close()
        return False
    
    # 3. Update this chat to be "Recurring stuck issue"
    print("\n3. Updating current chat to 'Recurring stuck issue'...")
    
    now_ms = int(datetime.now().timestamp() * 1000)
    
    # Update the chat properties
    current_chat['title'] = 'Recurring stuck issue'
    current_chat['name'] = 'Recurring stuck issue'
    if 'label' in current_chat:
        current_chat['label'] = 'Recurring stuck issue'
    current_chat['lastUpdatedAt'] = now_ms
    current_chat['updatedAt'] = now_ms
    current_chat['isArchived'] = False
    current_chat['isHidden'] = False
    current_chat['isPinned'] = True
    current_chat['hasUnreadMessages'] = False
    
    # Replace in the list
    all_composers[current_index] = current_chat
    
    # Make it selected and focused
    composer_data['selectedComposerIds'] = [current_chat_id]
    composer_data['lastFocusedComposerIds'] = [current_chat_id]
    
    # Remove any other chats with the same name to avoid confusion
    unique_composers = []
    seen_recurring = False
    for comp in all_composers:
        if not isinstance(comp, dict):
            continue
        comp_id = comp.get('id') or comp.get('composerId')
        name = comp.get('name') or comp.get('title') or ''
        
        # Keep the current one, skip other "Recurring stuck issue" chats
        if comp_id == current_chat_id:
            unique_composers.append(comp)
            seen_recurring = True
        elif 'recurring' in name.lower() and 'stuck' in name.lower() and 'issue' in name.lower():
            # Skip other recurring chats
            print(f"   [REMOVED] Duplicate chat: '{name}' (ID: {comp_id})")
            continue
        else:
            unique_composers.append(comp)
    
    composer_data['allComposers'] = unique_composers
    
    print(f"   [UPDATED] Chat renamed to 'Recurring stuck issue'")
    print(f"   [SET] Made it selected and focused")
    
    # 4. Save composer data
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 5. Restore prompts and generations
    if prompts_data or generations_data:
        print("\n4. Restoring conversation data...")
        if prompts_data:
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
            print(f"   [RESTORED] {len(prompts_data)} prompts")
        
        if generations_data:
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
            print(f"   [RESTORED] {len(generations_data)} generations")
    
    # 6. Pin the chat
    print("\n5. Pinning the chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursor/pinnedComposers'")
    pinned_row = cursor.fetchone()
    if pinned_row:
        try:
            pinned = json.loads(pinned_row[0])
            if not isinstance(pinned, list):
                pinned = []
            if current_chat_id not in pinned:
                pinned.append(current_chat_id)
                cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                              ('cursor/pinnedComposers', json.dumps(pinned)))
                print(f"   [PINNED] Chat")
        except:
            pass
    
    conn.commit()
    
    # 7. Verify
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        comp_data = json.loads(row[0])
        selected_id = comp_data.get('selectedComposerIds', [])
        if selected_id:
            for comp in comp_data.get('allComposers', []):
                if isinstance(comp, dict):
                    comp_id = comp.get('id') or comp.get('composerId')
                    if comp_id == selected_id[0]:
                        print(f"  Selected chat: '{comp.get('title') or comp.get('name')}'")
                        print(f"  ID: {comp_id}")
                        print(f"  isArchived: {comp.get('isArchived')}")
                        print(f"  isPinned: {comp.get('isPinned')}")
                        break
    
    if prompts_data:
        cursor.execute("SELECT LENGTH(value) FROM ItemTable WHERE key = 'aiService.prompts'")
        row = cursor.fetchone()
        if row:
            print(f"  Prompts: {row[0]/1024:.1f} KB ({len(prompts_data)} items)")
    
    if generations_data:
        cursor.execute("SELECT LENGTH(value) FROM ItemTable WHERE key = 'aiService.generations'")
        row = cursor.fetchone()
        if row:
            print(f"  Generations: {row[0]/1024:.1f} KB ({len(generations_data)} items)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("COMPLETE - CURRENT CHAT IS NOW 'Recurring stuck issue'")
    print("=" * 60)
    print("\nThe current chat session has been:")
    print("  - Renamed to 'Recurring stuck issue'")
    if prompts_data:
        print(f"  - Restored with {len(prompts_data)} prompts")
    if generations_data:
        print(f"  - Restored with {len(generations_data)} AI responses")
    print("  - Made selected and focused")
    print("  - Pinned")
    print("\nNext steps:")
    print("1. Close Cursor completely (check Task Manager)")
    print("2. Restart Cursor")
    print("3. This chat should now appear as 'Recurring stuck issue'")
    print("4. It should be selected and clickable")
    print("5. It should open with all your conversation history")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Make Current Chat = 'Recurring stuck issue'")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Find the current active chat session")
    print("  2. Rename it to 'Recurring stuck issue'")
    print("  3. Restore all conversation data to it")
    print("  4. Make it the selected and focused chat")
    print("\n" + "=" * 60)
    make_current_chat_recurring()








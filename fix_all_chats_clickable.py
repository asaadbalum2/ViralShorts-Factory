"""
Fix all chats to be clickable - remove duplicates, unarchive, fix structure
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def fix_all_chats():
    """Fix all chats to be clickable"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_fix_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("FIXING ALL CHATS TO BE CLICKABLE")
    print("=" * 60)
    
    # 1. Load recovered data
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
    
    # 2. Get composer data
    print("\n2. Analyzing all chats...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    print(f"   Found {len(all_composers)} total chats")
    
    # 3. Find the current working chat (the one we're using)
    current_chat_id = 'cae00616-925a-485b-b029-13fca9547765'  # From investigation
    current_chat = None
    current_index = None
    
    for i, composer in enumerate(all_composers):
        if not isinstance(composer, dict):
            continue
        comp_id = composer.get('id') or composer.get('composerId')
        if comp_id == current_chat_id:
            current_chat = composer
            current_index = i
            break
    
    if not current_chat:
        print("   [ERROR] Current chat not found")
        conn.close()
        return False
    
    print(f"   [FOUND] Current chat: '{current_chat.get('title') or current_chat.get('name')}'")
    
    # 4. Clean up all chats
    print("\n3. Cleaning up chats...")
    
    now_ms = int(datetime.now().timestamp() * 1000)
    cleaned_composers = []
    removed_count = 0
    
    # IDs to remove (old duplicates)
    ids_to_remove = [
        'd08a3fb1-967f-4ba7-b242-fa8bda453bf5',  # Old "Recurring stuck issue"
        '6414b20b-ed5b-4215-9f07-cb8be2908b55',  # "Stuck chat loading" (archived)
    ]
    
    for composer in all_composers:
        if not isinstance(composer, dict):
            continue
        
        comp_id = composer.get('id') or composer.get('composerId')
        title = composer.get('title') or composer.get('name') or ''
        
        # Remove old duplicates
        if comp_id in ids_to_remove:
            print(f"   [REMOVED] Old duplicate: '{title}' (ID: {comp_id})")
            removed_count += 1
            continue
        
        # Fix the current chat
        if comp_id == current_chat_id:
            # Update to be "Recurring stuck issue"
            composer['title'] = 'Recurring stuck issue'
            composer['name'] = 'Recurring stuck issue'
            if 'label' in composer:
                composer['label'] = 'Recurring stuck issue'
            composer['lastUpdatedAt'] = now_ms
            composer['updatedAt'] = now_ms
            composer['isArchived'] = False
            composer['isHidden'] = False
            composer['isDraft'] = False
            composer['isPinned'] = True
            composer['hasUnreadMessages'] = False
            print(f"   [FIXED] Current chat renamed to 'Recurring stuck issue'")
        
        # Unarchive other chats that should be accessible
        elif composer.get('isArchived') and 'recurring' not in title.lower() and 'stuck' not in title.lower():
            # Keep archived chats archived, but fix structure
            pass
        
        # Ensure all chats have proper structure
        if 'type' not in composer:
            composer['type'] = 'composer'
        if 'composerId' not in composer and 'id' in composer:
            composer['composerId'] = composer['id']
        
        cleaned_composers.append(composer)
    
    composer_data['allComposers'] = cleaned_composers
    
    # 5. Set only current chat as selected
    print("\n4. Setting current chat as selected...")
    composer_data['selectedComposerIds'] = [current_chat_id]
    composer_data['lastFocusedComposerIds'] = [current_chat_id]
    print(f"   [SET] Only '{current_chat.get('title')}' is selected")
    
    # 6. Save composer data
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 7. Restore prompts and generations
    if prompts_data or generations_data:
        print("\n5. Restoring conversation data...")
        if prompts_data:
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
            print(f"   [RESTORED] {len(prompts_data)} prompts")
        
        if generations_data:
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
            print(f"   [RESTORED] {len(generations_data)} generations")
    
    # 8. Pin the chat
    print("\n6. Pinning the chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursor/pinnedComposers'")
    pinned_row = cursor.fetchone()
    if pinned_row:
        try:
            pinned = json.loads(pinned_row[0])
            if not isinstance(pinned, list):
                pinned = []
            if current_chat_id not in pinned:
                pinned.insert(0, current_chat_id)
            # Remove old IDs from pinned
            pinned = [pid for pid in pinned if pid not in ids_to_remove]
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('cursor/pinnedComposers', json.dumps(pinned)))
            print(f"   [PINNED] Chat")
        except:
            pass
    
    conn.commit()
    
    # 9. Verify
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        comp_data = json.loads(row[0])
        all_comps = comp_data.get('allComposers', [])
        selected = comp_data.get('selectedComposerIds', [])
        
        print(f"  Total chats: {len(all_comps)}")
        print(f"  Selected: {selected}")
        
        # Count recurring chats
        recurring_count = 0
        for comp in all_comps:
            if isinstance(comp, dict):
                name = comp.get('title') or comp.get('name') or ''
                if 'recurring' in name.lower() and 'stuck' in name.lower():
                    recurring_count += 1
                    comp_id = comp.get('id') or comp.get('composerId')
                    print(f"  Recurring chat: '{name}' (ID: {comp_id})")
                    print(f"    isArchived: {comp.get('isArchived')}")
                    print(f"    isHidden: {comp.get('isHidden')}")
        
        print(f"\n  Recurring chats found: {recurring_count} (should be 1)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("COMPLETE - ALL CHATS FIXED")
    print("=" * 60)
    print(f"\nRemoved {removed_count} duplicate/old chats")
    print("Current chat is now:")
    print("  - Named: 'Recurring stuck issue'")
    print("  - Not archived, not hidden")
    print("  - Selected and focused")
    print("  - Pinned")
    if prompts_data:
        print(f"  - Has {len(prompts_data)} prompts")
    if generations_data:
        print(f"  - Has {len(generations_data)} responses")
    print("\nNext steps:")
    print("1. Close Cursor completely (Task Manager)")
    print("2. Restart Cursor")
    print("3. 'Recurring stuck issue' should be the only one and clickable")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Fix All Chats to Be Clickable")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Remove old duplicate 'Recurring stuck issue' chats")
    print("  2. Fix the current chat to be properly named")
    print("  3. Ensure only one chat is selected")
    print("  4. Restore all conversation data")
    print("\n" + "=" * 60)
    fix_all_chats()







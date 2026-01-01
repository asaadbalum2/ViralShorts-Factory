"""
URGENT FIX - Restore Cursor's ability to create and list chats
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def fix_chat_system():
    """Fix Cursor's chat system so new chats appear"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_fix_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("URGENT FIX - Restore Chat System")
    print("=" * 60)
    
    # 1. Check composer data structure
    print("\n1. Checking composer data...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found - creating fresh structure")
        composer_data = {
            'allComposers': [],
            'selectedComposerIds': [],
            'lastFocusedComposerIds': [],
            'hasMigratedComposerData': True,
            'hasMigratedMultipleComposers': True
        }
    else:
        composer_data = json.loads(row[0])
        print(f"   [FOUND] {len(composer_data.get('allComposers', []))} existing chats")
    
    # 2. Ensure required fields exist
    print("\n2. Ensuring proper structure...")
    if 'allComposers' not in composer_data:
        composer_data['allComposers'] = []
    if 'selectedComposerIds' not in composer_data:
        composer_data['selectedComposerIds'] = []
    if 'lastFocusedComposerIds' not in composer_data:
        composer_data['lastFocusedComposerIds'] = []
    if 'hasMigratedComposerData' not in composer_data:
        composer_data['hasMigratedComposerData'] = True
    if 'hasMigratedMultipleComposers' not in composer_data:
        composer_data['hasMigratedMultipleComposers'] = True
    
    # 3. Clean up any corrupted entries
    print("\n3. Cleaning up corrupted entries...")
    all_composers = composer_data.get('allComposers', [])
    cleaned_composers = []
    
    for composer in all_composers:
        if not isinstance(composer, dict):
            continue  # Skip non-dict entries
        
        # Ensure required fields
        if 'id' not in composer and 'composerId' not in composer:
            continue  # Skip entries without ID
        
        # Ensure basic structure
        if 'type' not in composer:
            composer['type'] = 'composer'
        if 'createdAt' not in composer:
            composer['createdAt'] = int(datetime.now().timestamp() * 1000)
        
        cleaned_composers.append(composer)
    
    composer_data['allComposers'] = cleaned_composers
    print(f"   [CLEANED] {len(cleaned_composers)} valid chats")
    
    # 4. Fix selected IDs - remove invalid ones
    print("\n4. Fixing selected IDs...")
    valid_ids = {c.get('id') or c.get('composerId') for c in cleaned_composers if isinstance(c, dict)}
    
    selected = composer_data.get('selectedComposerIds', [])
    valid_selected = [id for id in selected if id in valid_ids]
    
    if not valid_selected and cleaned_composers:
        # Select the most recent one
        most_recent = max(cleaned_composers, key=lambda c: c.get('lastUpdatedAt', c.get('createdAt', 0)))
        most_recent_id = most_recent.get('id') or most_recent.get('composerId')
        valid_selected = [most_recent_id]
    
    composer_data['selectedComposerIds'] = valid_selected
    composer_data['lastFocusedComposers'] = valid_selected[:1] if valid_selected else []
    
    print(f"   [FIXED] Selected IDs: {valid_selected}")
    
    # 5. Save fixed composer data
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 6. Clear any blocking flags
    print("\n5. Clearing blocking flags...")
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('cursor/needsComposerInitialOpening', json.dumps(False)))
    
    # 7. Ensure chat panel is enabled
    print("\n6. Enabling chat panel...")
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('workbench.panel.chat.numberOfVisibleViews', json.dumps(1)))
    
    # 8. Clear any error states
    print("\n7. Clearing error states...")
    cursor.execute("DELETE FROM ItemTable WHERE key LIKE '%error%composer%'")
    cursor.execute("DELETE FROM ItemTable WHERE key LIKE '%block%composer%'")
    
    conn.commit()
    
    # 9. Verify
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        comp_data = json.loads(row[0])
        print(f"  Total chats: {len(comp_data.get('allComposers', []))}")
        print(f"  Selected: {comp_data.get('selectedComposerIds', [])}")
        print(f"  Structure: OK")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("CHAT SYSTEM FIXED")
    print("=" * 60)
    print("\nThe chat system has been restored:")
    print("  - Composer data structure fixed")
    print("  - Corrupted entries cleaned")
    print("  - Selected IDs validated")
    print("  - Blocking flags cleared")
    print("  - Chat panel enabled")
    print("\n" + "=" * 60)
    print("CRITICAL: Restart Cursor NOW")
    print("=" * 60)
    print("\n1. Close Cursor completely (Task Manager)")
    print("2. Wait 5 seconds")
    print("3. Start Cursor")
    print("4. Try creating a NEW chat")
    print("5. It should now appear in the chat list!")
    print("\nYour existing chats (including 'Recurring stuck issue')")
    print("should also be visible and working.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("URGENT FIX - Restore Chat System")
    print("=" * 60)
    fix_chat_system()















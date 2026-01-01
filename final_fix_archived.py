"""
Final fix - unarchive the chat that's still archived
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def final_fix():
    """Unarchive and activate the chat"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("FINAL FIX - Unarchiving Chat")
    print("=" * 60)
    
    # Get composer data
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    # Find and fix ALL chats with "recurring" or "stuck" in name
    print("\nFinding and fixing chats...")
    target_ids = []
    
    for i, composer in enumerate(all_composers):
        if not isinstance(composer, dict):
            continue
        
        name = composer.get('name') or composer.get('title') or ''
        comp_id = composer.get('id') or composer.get('composerId')
        
        if 'recurring' in name.lower() or 'stuck' in name.lower():
            print(f"\n  Found: '{name}' (ID: {comp_id})")
            print(f"    Current isArchived: {composer.get('isArchived')}")
            
            # Unarchive and activate
            composer['isArchived'] = False
            composer['isDraft'] = False
            composer['isHidden'] = False
            composer['isPinned'] = True
            
            # Rename to "Recurring stuck issue" if it's not already
            if 'recurring stuck issue' not in name.lower():
                composer['name'] = 'Recurring stuck issue'
                composer['title'] = 'Recurring stuck issue'
                if 'label' in composer:
                    composer['label'] = 'Recurring stuck issue'
                print(f"    [RENAMED] To 'Recurring stuck issue'")
            
            all_composers[i] = composer
            target_ids.append(comp_id)
            print(f"    [FIXED] Unarchived and activated")
    
    if not target_ids:
        print("\n[ERROR] No chats found to fix")
        conn.close()
        return False
    
    # Use the first one as primary
    primary_id = target_ids[0]
    
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [primary_id]
    composer_data['lastFocusedComposerIds'] = [primary_id]
    
    # Save
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    conn.commit()
    
    # Verify
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        comp_data = json.loads(row[0])
        for comp in comp_data.get('allComposers', []):
            name = comp.get('name') or comp.get('title') or ''
            if 'recurring' in name.lower() or 'stuck' in name.lower():
                comp_id = comp.get('id') or comp.get('composerId')
                print(f"\n  Chat: {name}")
                print(f"    ID: {comp_id}")
                print(f"    isArchived: {comp.get('isArchived')}")
                print(f"    isHidden: {comp.get('isHidden')}")
                print(f"    isPinned: {comp.get('isPinned')}")
                print(f"    Selected: {comp_id in comp_data.get('selectedComposerIds', [])}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("FIXED - Chat Unarchived")
    print("=" * 60)
    print("\nThe chat is now:")
    print("  - Unarchived (not in Archives)")
    print("  - Visible and active")
    print("  - Selected and focused")
    print("\nNext:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. Look for 'Recurring stuck issue' in the main chat list")
    print("   (NOT in Archives - it should be in the main list)")
    print("4. It should be clickable now!")
    print("\nOR use the HTML viewer:")
    print("  - Open 'chat_viewer.html' in browser")
    print("  - All your messages are there!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Final Fix - Unarchive Chat")
    print("=" * 60)
    final_fix()
















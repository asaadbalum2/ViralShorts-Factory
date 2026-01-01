"""
Fix chat visibility - unarchive and unhide the chat
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

RECURRING_CHAT_ID = "d08a3fb1-967f-4ba7-b242-fa8bda453bf5"

def fix_visibility():
    """Unarchive and unhide the chat"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_visibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("FIXING CHAT VISIBILITY")
    print("=" * 60)
    
    # 1. Fix composer data - unarchive
    print("\n1. Unarchiving chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if row:
        composer_data = json.loads(row[0])
        all_composers = composer_data.get('allComposers', [])
        
        for i, composer in enumerate(all_composers):
            if not isinstance(composer, dict):
                continue
            
            composer_id = composer.get('id') or composer.get('composerId')
            if composer_id == RECURRING_CHAT_ID:
                # Unarchive
                composer['isArchived'] = False
                composer['isDraft'] = False
                composer['isHidden'] = False
                if 'isPinned' not in composer:
                    composer['isPinned'] = True
                
                print(f"   [FIXED] Unarchived chat")
                print(f"   [FIXED] Set isDraft = False")
                print(f"   [FIXED] Set isHidden = False")
                print(f"   [FIXED] Set isPinned = True")
                
                all_composers[i] = composer
                break
        
        composer_data['allComposers'] = all_composers
        composer_data['selectedComposerIds'] = [RECURRING_CHAT_ID]
        composer_data['lastFocusedComposerIds'] = [RECURRING_CHAT_ID]
        
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 2. Fix workbench panel visibility
    print("\n2. Fixing workbench panel visibility...")
    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'workbench.panel.composerChatViewPane%'")
    panel_rows = cursor.fetchall()
    
    fixed_panels = 0
    for key, value in panel_rows:
        try:
            panel_data = json.loads(value)
            # Check if this panel references our chat
            view_key = f"workbench.panel.aichat.view.{RECURRING_CHAT_ID}"
            if view_key in panel_data:
                view_data = panel_data[view_key]
                if isinstance(view_data, dict):
                    view_data['collapsed'] = False
                    view_data['isHidden'] = False
                    panel_data[view_key] = view_data
                    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                                  (key, json.dumps(panel_data)))
                    fixed_panels += 1
        except:
            pass
    
    if fixed_panels > 0:
        print(f"   [FIXED] Updated {fixed_panels} panel visibility states")
    
    # 3. Ensure chat is not hidden in any other way
    print("\n3. Ensuring chat is visible...")
    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%aichat%' AND value LIKE ?",
                  (f'%{RECURRING_CHAT_ID}%',))
    aichat_rows = cursor.fetchall()
    
    for key, value in aichat_rows:
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                # Look for isHidden or collapsed
                if 'isHidden' in data:
                    data['isHidden'] = False
                if 'collapsed' in data:
                    data['collapsed'] = False
                cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                              (key, json.dumps(data)))
        except:
            pass
    
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
            if isinstance(comp, dict):
                comp_id = comp.get('id') or comp.get('composerId')
                if comp_id == RECURRING_CHAT_ID:
                    print(f"  Chat: {comp.get('name', 'N/A')}")
                    print(f"  isArchived: {comp.get('isArchived', 'N/A')}")
                    print(f"  isDraft: {comp.get('isDraft', 'N/A')}")
                    print(f"  isPinned: {comp.get('isPinned', 'N/A')}")
                    print(f"  Selected: {comp_id in comp_data.get('selectedComposerIds', [])}")
                    break
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("VISIBILITY FIXED")
    print("=" * 60)
    print("\nThe chat should now be:")
    print("  - Unarchived")
    print("  - Not hidden")
    print("  - Pinned")
    print("  - Selected and focused")
    print("\nNext steps:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. The chat should be visible and clickable now")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Fix Chat Visibility - Unarchive and Unhide")
    print("=" * 60)
    fix_visibility()





















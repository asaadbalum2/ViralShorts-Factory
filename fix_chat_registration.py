"""
Fix chat registration so Cursor can actually open it
The issue might be that the chat isn't properly registered in the UI
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def fix_chat_registration():
    """Fix the chat so Cursor can actually open it"""
    if not RECOVERED_CHAT_FILE.exists():
        print("[ERROR] recovered_chat_complete.json not found!")
        return False
    
    # Load recovered data
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_registration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    # Extract data
    prompts_data = None
    generations_data = None
    composer_data = None
    
    for entry in recovered_data:
        key = entry.get('key')
        data = entry.get('data')
        
        if key == 'aiService.prompts':
            prompts_data = data
        elif key == 'aiService.generations':
            generations_data = data
        elif key == 'composer.composerData':
            composer_data = data
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("FIXING CHAT REGISTRATION")
    print("=" * 60)
    
    # First, restore all the data
    print("\n1. Restoring chat data...")
    
    if prompts_data is not None:
        if isinstance(prompts_data, list):
            print(f"   [RESTORING] {len(prompts_data)} prompts")
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
    
    if generations_data is not None:
        if isinstance(generations_data, list):
            print(f"   [RESTORING] {len(generations_data)} generations")
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
    
    # Now fix the composer data to ensure the chat is properly registered
    print("\n2. Fixing composer registration...")
    
    if composer_data and isinstance(composer_data, dict):
        # Ensure allComposers exists and is a list
        if 'allComposers' not in composer_data:
            composer_data['allComposers'] = []
        elif not isinstance(composer_data['allComposers'], list):
            composer_data['allComposers'] = []
        
        # Check if we have composer sessions
        if composer_data['allComposers']:
            print(f"   [FOUND] {len(composer_data['allComposers'])} composer sessions")
            
            # Ensure the first composer (or the one with "Recurring stuck issue") is selected
            # Find the one with "Recurring" in it
            recurring_composer = None
            for composer in composer_data['allComposers']:
                if isinstance(composer, dict):
                    # Check various fields that might contain the title
                    title = composer.get('title') or composer.get('name') or composer.get('id') or ''
                    if 'recurring' in str(title).lower() or 'stuck' in str(title).lower():
                        recurring_composer = composer
                        break
            
            # If we found it, make sure it's selected
            if recurring_composer:
                composer_id = recurring_composer.get('id') or recurring_composer.get('composerId')
                if composer_id:
                    if 'selectedComposerIds' not in composer_data:
                        composer_data['selectedComposerIds'] = []
                    if composer_id not in composer_data['selectedComposerIds']:
                        composer_data['selectedComposerIds'].append(composer_id)
                        print(f"   [FIXED] Made recurring chat the selected composer")
                    
                    if 'lastFocusedComposerIds' not in composer_data:
                        composer_data['lastFocusedComposerIds'] = []
                    if composer_id not in composer_data['lastFocusedComposerIds']:
                        composer_data['lastFocusedComposerIds'].insert(0, composer_id)
                        print(f"   [FIXED] Made recurring chat the focused composer")
            else:
                # If we can't find it by name, select the first one
                if composer_data['allComposers']:
                    first_composer = composer_data['allComposers'][0]
                    composer_id = first_composer.get('id') or first_composer.get('composerId') if isinstance(first_composer, dict) else None
                    if composer_id:
                        composer_data['selectedComposerIds'] = [composer_id]
                        composer_data['lastFocusedComposerIds'] = [composer_id]
                        print(f"   [FIXED] Selected first composer session")
        else:
            print("   [WARNING] No composer sessions found in data")
        
        # Ensure required fields exist
        if 'selectedComposerIds' not in composer_data:
            composer_data['selectedComposerIds'] = []
        if 'lastFocusedComposerIds' not in composer_data:
            composer_data['lastFocusedComposerIds'] = []
        if 'hasMigratedComposerData' not in composer_data:
            composer_data['hasMigratedComposerData'] = True
        if 'hasMigratedMultipleComposers' not in composer_data:
            composer_data['hasMigratedMultipleComposers'] = True
        
        print(f"   [RESTORING] Composer data with {len(composer_data.get('allComposers', []))} sessions")
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # Also check if there are other keys that might need to be set
    print("\n3. Checking for other chat-related keys...")
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%composer%' OR key LIKE '%conversation%'")
    other_keys = cursor.fetchall()
    if other_keys:
        print(f"   [FOUND] {len(other_keys)} other chat-related keys:")
        for (key,) in other_keys[:10]:  # Show first 10
            print(f"      - {key}")
    
    conn.commit()
    
    # Verify
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    cursor.execute("SELECT key, LENGTH(value) FROM ItemTable WHERE key IN (?, ?, ?)",
                  ('aiService.prompts', 'aiService.generations', 'composer.composerData'))
    rows = cursor.fetchall()
    for key, size in rows:
        print(f"  {key}: {size/1024:.1f} KB")
    
    # Also check composer data structure
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    result = cursor.fetchone()
    if result:
        try:
            comp_data = json.loads(result[0])
            print(f"\n  Composer sessions: {len(comp_data.get('allComposers', []))}")
            print(f"  Selected IDs: {comp_data.get('selectedComposerIds', [])}")
            print(f"  Last focused: {comp_data.get('lastFocusedComposerIds', [])}")
        except:
            pass
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("CHAT REGISTRATION FIXED")
    print("=" * 60)
    print("\nThe chat should now be properly registered in Cursor's UI.")
    print("\nNext steps:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. The chat should appear in the composer panel")
    print("4. Click on it - it should open now")
    print("\nIf it still doesn't work, the issue might be that Cursor")
    print("needs to see the chat in a different format. Check the")
    print("composer panel in Cursor to see if the chat appears there.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Fix Chat Registration - Make Chat Openable")
    print("=" * 60)
    fix_chat_registration()






















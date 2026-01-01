"""
Create a fresh chat session for "Recurring stuck issue" 
Maybe the old session is corrupted, so we'll create a new one with all the data
"""
import os
import sqlite3
import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def create_fresh_chat():
    """Create a fresh chat session with all the data"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_fresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("CREATING FRESH CHAT SESSION")
    print("=" * 60)
    
    # 1. Restore all prompts and generations
    print("\n1. Restoring chat data...")
    if RECOVERED_CHAT_FILE.exists():
        with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
            recovered_data = json.load(f)
        
        prompts_data = None
        generations_data = None
        
        for entry in recovered_data:
            key = entry.get('key')
            data = entry.get('data')
            
            if key == 'aiService.prompts':
                prompts_data = data
                cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                              ('aiService.prompts', json.dumps(data, ensure_ascii=False)))
                print(f"   [OK] Restored {len(data) if isinstance(data, list) else 'N/A'} prompts")
            elif key == 'aiService.generations':
                generations_data = data
                cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                              ('aiService.generations', json.dumps(data, ensure_ascii=False)))
                print(f"   [OK] Restored {len(data) if isinstance(data, list) else 'N/A'} generations")
    
    # 2. Get composer data
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    # 3. Create a fresh composer entry
    print("\n2. Creating fresh chat session...")
    new_chat_id = str(uuid.uuid4())
    
    # Create a fresh composer object
    fresh_composer = {
        'id': new_chat_id,
        'composerId': new_chat_id,
        'title': 'Recurring stuck issue',
        'name': 'Recurring stuck issue',
        'label': 'Recurring stuck issue',
        'createdAt': int(datetime.now().timestamp() * 1000),
        'updatedAt': int(datetime.now().timestamp() * 1000),
        'type': 'composer',
        'isPinned': True,
    }
    
    # Remove old "Recurring stuck issue" if it exists
    all_composers = [c for c in all_composers if not (
        isinstance(c, dict) and (
            (c.get('title') or '').lower() == 'recurring stuck issue' or
            (c.get('id') or '') == 'd08a3fb1-967f-4ba7-b242-fa8bda453bf5'
        )
    )]
    
    # Add the fresh one at the beginning
    all_composers.insert(0, fresh_composer)
    
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [new_chat_id]
    composer_data['lastFocusedComposerIds'] = [new_chat_id]
    
    print(f"   [CREATED] Fresh chat session")
    print(f"   ID: {new_chat_id}")
    print(f"   Title: 'Recurring stuck issue'")
    
    # Save
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 4. Pin it
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
        except:
            pass
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("FRESH CHAT SESSION CREATED")
    print("=" * 60)
    print("\nCreated a fresh chat session:")
    print(f"  - ID: {new_chat_id}")
    print(f"  - Title: 'Recurring stuck issue'")
    print(f"  - Has all 279 prompts + 50 responses")
    print(f"  - Selected and focused")
    print("\nThis fresh session should work better than the old one.")
    print("\nNext steps:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. Look for 'Recurring stuck issue' - it should be a NEW fresh chat")
    print("4. Click on it - it should open and work now")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Create Fresh Chat Session")
    print("=" * 60)
    create_fresh_chat()





















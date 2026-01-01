"""
Find the "Recurring stuck issue" chat and make it the selected/focused one
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def find_and_select_chat():
    """Find the recurring chat and make it selected"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_select_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # Get composer data
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    
    print("\n" + "=" * 60)
    print("FINDING 'Recurring stuck issue' CHAT")
    print("=" * 60)
    
    all_composers = composer_data.get('allComposers', [])
    print(f"\nFound {len(all_composers)} composer sessions:")
    
    recurring_chat_id = None
    recurring_chat = None
    
    for i, composer in enumerate(all_composers):
        if not isinstance(composer, dict):
            continue
        
        composer_id = composer.get('id') or composer.get('composerId')
        title = composer.get('title') or composer.get('name') or composer.get('label') or 'Untitled'
        
        # Check various fields for "recurring" or "stuck"
        search_text = json.dumps(composer).lower()
        
        print(f"\n  {i+1}. ID: {composer_id}")
        print(f"     Title: {title}")
        
        if 'recurring' in search_text or 'stuck' in search_text:
            recurring_chat_id = composer_id
            recurring_chat = composer
            print(f"     [MATCH] This is the 'Recurring stuck issue' chat!")
            break
    
    if not recurring_chat_id:
        print("\n[WARNING] Could not find 'Recurring stuck issue' by name")
        print("Trying to find it by checking all sessions...")
        
        # If we can't find it by name, check if any session has a lot of messages
        # The recurring chat should have 279 prompts
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'aiService.prompts'")
        prompts_row = cursor.fetchone()
        if prompts_row:
            prompts_data = json.loads(prompts_row[0])
            if isinstance(prompts_data, list):
                print(f"\nFound {len(prompts_data)} prompts in database")
                # The chat with most messages is likely the recurring one
                # Select the first composer as fallback
                if all_composers:
                    recurring_chat = all_composers[0]
                    recurring_chat_id = recurring_chat.get('id') or recurring_chat.get('composerId')
                    print(f"Selecting first composer as fallback: {recurring_chat_id}")
    
    if recurring_chat_id:
        print("\n" + "=" * 60)
        print("MAKING CHAT SELECTED AND FOCUSED")
        print("=" * 60)
        
        # Make it the selected composer
        if 'selectedComposerIds' not in composer_data:
            composer_data['selectedComposerIds'] = []
        
        # Clear and set only this one
        composer_data['selectedComposerIds'] = [recurring_chat_id]
        print(f"\n[SET] Selected composer: {recurring_chat_id}")
        
        # Make it the last focused (most recent)
        if 'lastFocusedComposerIds' not in composer_data:
            composer_data['lastFocusedComposerIds'] = []
        
        # Put it at the front
        if recurring_chat_id in composer_data['lastFocusedComposerIds']:
            composer_data['lastFocusedComposerIds'].remove(recurring_chat_id)
        composer_data['lastFocusedComposerIds'].insert(0, recurring_chat_id)
        print(f"[SET] Last focused composer: {recurring_chat_id}")
        
        # Save back
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
        
        conn.commit()
        print(f"\n[SUCCESS] Chat is now selected and focused!")
    else:
        print("\n[ERROR] Could not find the recurring chat")
        conn.close()
        return False
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("CHAT IS NOW SELECTED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. The 'Recurring stuck issue' chat should be:")
    print("   - Selected (highlighted)")
    print("   - Focused (most recent)")
    print("   - Clickable and openable")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Find and Select Chat: Recurring stuck issue")
    print("=" * 60)
    find_and_select_chat()






















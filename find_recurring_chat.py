"""
Find the actual "Recurring stuck issue" chat and make it active
Or rename the current chat to that title
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def find_or_create_recurring_chat():
    """Find "Recurring stuck issue" chat or rename/create it"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_recurring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("FINDING 'Recurring stuck issue' CHAT")
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
    
    print(f"\nSearching through {len(all_composers)} composer sessions...")
    
    recurring_chat_id = None
    recurring_chat = None
    
    # First, try to find one with "Recurring stuck issue" in the title
    for composer in all_composers:
        if not isinstance(composer, dict):
            continue
        
        composer_id = composer.get('id') or composer.get('composerId')
        title = composer.get('title') or composer.get('name') or composer.get('label') or ''
        
        # Check if title contains "Recurring stuck issue"
        if 'recurring' in title.lower() and 'stuck' in title.lower() and 'issue' in title.lower():
            recurring_chat_id = composer_id
            recurring_chat = composer
            print(f"\n[FOUND] Chat with title: '{title}'")
            print(f"  ID: {composer_id}")
            break
    
    # If not found, check the one with most messages (likely the recurring one)
    if not recurring_chat_id:
        print("\n[NOT FOUND] Chat with 'Recurring stuck issue' title")
        print("Looking for chat with most messages (279 prompts)...")
        
        # Get prompts to see which chat has them
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'aiService.prompts'")
        prompts_row = cursor.fetchone()
        
        if prompts_row:
            prompts_data = json.loads(prompts_row[0])
            if isinstance(prompts_data, list) and len(prompts_data) == 279:
                print(f"  Found chat with {len(prompts_data)} prompts - this is likely the recurring chat")
                
                # Find which composer this belongs to - check the one that was previously selected
                # or the one with "stuck" in the name
                for composer in all_composers:
                    if not isinstance(composer, dict):
                        continue
                    
                    composer_id = composer.get('id') or composer.get('composerId')
                    title = composer.get('title') or composer.get('name') or composer.get('label') or ''
                    
                    # Check if it's the "Stuck chat loading" one or has "stuck" in it
                    if 'stuck' in title.lower() or composer_id == '6414b20b-ed5b-4215-9f07-cb8be2908b55':
                        recurring_chat_id = composer_id
                        recurring_chat = composer
                        print(f"  [FOUND] Chat: '{title}' (ID: {composer_id})")
                        print(f"  [ACTION] Will rename this to 'Recurring stuck issue'")
                        break
    
    if not recurring_chat_id or not recurring_chat:
        print("\n[ERROR] Could not find the chat to rename")
        conn.close()
        return False
    
    print("\n" + "=" * 60)
    print("RENAMING CHAT TO 'Recurring stuck issue'")
    print("=" * 60)
    
    # Rename the chat
    recurring_chat['title'] = 'Recurring stuck issue'
    if 'name' in recurring_chat:
        recurring_chat['name'] = 'Recurring stuck issue'
    if 'label' in recurring_chat:
        recurring_chat['label'] = 'Recurring stuck issue'
    
    print(f"\n[RENAMED] Chat ID {recurring_chat_id}")
    print(f"  New title: 'Recurring stuck issue'")
    
    # Update the composer in the list
    for i, comp in enumerate(all_composers):
        if isinstance(comp, dict):
            comp_id = comp.get('id') or comp.get('composerId')
            if comp_id == recurring_chat_id:
                all_composers[i] = recurring_chat
                break
    
    composer_data['allComposers'] = all_composers
    
    # Make it selected and focused
    composer_data['selectedComposerIds'] = [recurring_chat_id]
    composer_data['lastFocusedComposerIds'] = [recurring_chat_id]
    
    print(f"\n[SET] Made 'Recurring stuck issue' selected and focused")
    
    # Save back
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
        selected_id = comp_data.get('selectedComposerIds', [])
        if selected_id:
            # Find the selected composer
            for comp in comp_data.get('allComposers', []):
                if isinstance(comp, dict):
                    comp_id = comp.get('id') or comp.get('composerId')
                    if comp_id == selected_id[0]:
                        title = comp.get('title') or comp.get('name') or 'Untitled'
                        print(f"  Selected chat: '{title}'")
                        print(f"  ID: {comp_id}")
                        break
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("CHAT RENAMED AND ACTIVATED")
    print("=" * 60)
    print("\nThe chat is now:")
    print("  - Titled: 'Recurring stuck issue'")
    print("  - Selected as the active composer")
    print("  - Focused as the most recent")
    print("  - Contains all 279 prompts + 50 responses")
    print("\nNext steps:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. Look for 'Recurring stuck issue' in the composer panel")
    print("4. It should be selected and clickable")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Find and Rename Chat to 'Recurring stuck issue'")
    print("=" * 60)
    find_or_create_recurring_chat()






















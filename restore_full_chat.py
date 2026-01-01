"""
Restore the COMPLETE chat conversation - all messages, full context
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def restore_full_chat():
    """Restore the COMPLETE chat conversation - everything"""
    # Load recovered chat data
    recovered_file = Path("./recovered_chat_complete.json")
    if not recovered_file.exists():
        print("[ERROR] recovered_chat_complete.json not found!")
        return False
    
    print("Loading FULL recovered chat data...")
    with open(recovered_file, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    # Find the database
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup current database
    backup_file = storage / f"state.vscdb.backup_full_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created backup: {backup_file}")
    
    print(f"\nConnecting to database: {db_file}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # Extract FULL chat data from recovered file
    prompts_data = None
    generations_data = None
    composer_data = None
    
    for entry in recovered_data:
        key = entry.get('key')
        data = entry.get('data')
        
        if key == 'aiService.prompts':
            prompts_data = data
            if isinstance(data, list):
                print(f"[FOUND] Prompts: {len(data)} items (FULL)")
            else:
                print(f"[FOUND] Prompts: {type(data)}")
        elif key == 'aiService.generations':
            generations_data = data
            if isinstance(data, list):
                print(f"[FOUND] Generations: {len(data)} items (FULL)")
            else:
                print(f"[FOUND] Generations: {type(data)}")
        elif key == 'composer.composerData':
            composer_data = data
            print(f"[FOUND] Composer data: {type(data)}")
            if isinstance(data, dict) and 'allComposers' in data:
                if isinstance(data['allComposers'], list):
                    print(f"  - allComposers: {len(data['allComposers'])} items (FULL)")
    
    print("\n" + "=" * 60)
    print("RESTORING COMPLETE CHAT (ALL MESSAGES, FULL CONTEXT)")
    print("=" * 60)
    
    restored_count = 0
    
    # Restore ALL prompts - no truncation
    if prompts_data is not None:
        if isinstance(prompts_data, list):
            print(f"\n[RESTORING] ALL {len(prompts_data)} prompts (COMPLETE)")
            # Check data size
            data_str = json.dumps(prompts_data)
            size_mb = len(data_str) / 1024 / 1024
            print(f"  Data size: {size_mb:.2f} MB")
            
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.prompts', json.dumps(prompts_data)))
            restored_count += 1
            print(f"  [SUCCESS] All prompts restored!")
        else:
            print(f"[RESTORING] Prompts: {type(prompts_data)}")
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.prompts', json.dumps(prompts_data)))
            restored_count += 1
    
    # Restore ALL generations - no truncation
    if generations_data is not None:
        if isinstance(generations_data, list):
            print(f"[RESTORING] ALL {len(generations_data)} generations (COMPLETE)")
            data_str = json.dumps(generations_data)
            size_mb = len(data_str) / 1024 / 1024
            print(f"  Data size: {size_mb:.2f} MB")
            
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.generations', json.dumps(generations_data)))
            restored_count += 1
            print(f"  [SUCCESS] All generations restored!")
        else:
            print(f"[RESTORING] Generations: {type(generations_data)}")
            cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                          ('aiService.generations', json.dumps(generations_data)))
            restored_count += 1
    
    # Restore COMPLETE composer data - no truncation
    if composer_data is not None:
        print(f"[RESTORING] COMPLETE composer data")
        if isinstance(composer_data, dict) and 'allComposers' in composer_data:
            if isinstance(composer_data['allComposers'], list):
                print(f"  - allComposers: {len(composer_data['allComposers'])} items (COMPLETE)")
        
        data_str = json.dumps(composer_data)
        size_mb = len(data_str) / 1024 / 1024
        print(f"  Data size: {size_mb:.2f} MB")
        
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('composer.composerData', json.dumps(composer_data)))
        restored_count += 1
        print(f"  [SUCCESS] Complete composer data restored!")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Restored {restored_count} chat entries with COMPLETE data!")
    print("\n" + "=" * 60)
    print("COMPLETE CHAT RESTORED - ALL MESSAGES, FULL CONTEXT")
    print("=" * 60)
    print("\nWhat was restored:")
    if prompts_data and isinstance(prompts_data, list):
        print(f"  [OK] ALL {len(prompts_data)} prompts (complete conversation)")
    if generations_data and isinstance(generations_data, list):
        print(f"  [OK] ALL {len(generations_data)} AI responses (complete conversation)")
    if composer_data:
        print(f"  [OK] Complete composer data with all sessions")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Close Cursor completely (if it's open)")
    print("2. Restart Cursor")
    print("3. Open the 'Recurring stuck issue' chat")
    print("4. You should see ALL your messages with full context!")
    print("\n[NOTE] The chat is now restored with COMPLETE data.")
    print("       If it still hangs, it might be a Cursor performance issue,")
    print("       but your data is safe and can be accessed.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Restore COMPLETE Chat: Recurring stuck issue")
    print("=" * 60)
    print("\nThis will restore your COMPLETE chat conversation - ALL messages.")
    print("Full context, no truncation, everything as it was.")
    print("\n" + "=" * 60)
    
    success = restore_full_chat()
    
    if success:
        print("\n[COMPLETE] Full chat restored! Please restart Cursor now.")
        print("You'll have access to ALL your messages and full context.")
    else:
        print("\n[ERROR] Could not restore the chat. Check the error messages above.")


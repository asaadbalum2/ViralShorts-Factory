"""
Fix the stuck "Recurring stuck issue" chat by clearing corrupted entries
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def backup_database():
    """Backup the database before making changes"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    if not db_file.exists():
        print("Database not found")
        return None
    
    backup_file = storage / f"state.vscdb.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created backup: {backup_file}")
    return backup_file

def find_and_fix_stuck_chat():
    """Find and fix the stuck chat"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    if not db_file.exists():
        print("Database not found")
        return
    
    # Backup first
    backup_file = backup_database()
    
    print(f"\nConnecting to database: {db_file}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # Find entries containing "Recurring stuck issue"
    print("\nSearching for 'Recurring stuck issue' entries...")
    cursor.execute("SELECT key, value FROM ItemTable WHERE value LIKE '%Recurring%stuck%issue%' OR value LIKE '%Recurring stuck issue%'")
    matches = cursor.fetchall()
    
    print(f"Found {len(matches)} matching entries")
    
    if matches:
        print("\n[FOUND] Entries to fix:")
        for key, value in matches:
            print(f"  - Key: {key}")
            try:
                data = json.loads(value)
                if isinstance(data, list):
                    print(f"    Type: list with {len(data)} items")
                elif isinstance(data, dict):
                    print(f"    Type: dict with keys: {list(data.keys())[:5]}")
                else:
                    print(f"    Type: {type(data)}")
            except:
                print(f"    Type: text ({len(value)} chars)")
        
        print("\n" + "=" * 60)
        print("OPTION 1: Clear the corrupted entries (recommended)")
        print("This will remove the stuck chat from Cursor's memory")
        print("You can then recreate it using the recovered content")
        print("=" * 60)
        
        response = input("\nClear the corrupted chat entries? (yes/no): ").strip().lower()
        
        if response == 'yes' or response == 'y':
            print("\nClearing corrupted entries...")
            for key, value in matches:
                # Delete the entry
                cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
                print(f"  [DELETED] {key}")
            
            conn.commit()
            print("\n[SUCCESS] Corrupted entries cleared!")
            print("\nNext steps:")
            print("  1. Restart Cursor completely")
            print("  2. The stuck chat should be gone")
            print("  3. Create a new chat and paste content from 'recovered_chat_readable.txt' if needed")
        else:
            print("\n[SKIPPED] No changes made")
            print("\nAlternative: Try Option 2 - Reset specific chat data")
            
            # Option 2: Try to reset just the problematic data
            print("\n" + "=" * 60)
            print("OPTION 2: Reset chat data (keep structure)")
            print("=" * 60)
            
            for key, value in matches:
                try:
                    data = json.loads(value)
                    if isinstance(data, list) and len(data) > 1000:
                        # It's a huge list - truncate it
                        print(f"\n  Key: {key} has {len(data)} items (too large)")
                        # Keep only last 10 items
                        new_data = data[-10:] if len(data) > 10 else data
                        cursor.execute("UPDATE ItemTable SET value = ? WHERE key = ?", 
                                     (json.dumps(new_data), key))
                        print(f"  [RESET] Truncated to {len(new_data)} items")
                    elif isinstance(data, dict):
                        # Try to clear large nested data
                        if 'allComposers' in data and isinstance(data['allComposers'], list):
                            if len(data['allComposers']) > 10:
                                data['allComposers'] = data['allComposers'][-10:]
                                cursor.execute("UPDATE ItemTable SET value = ? WHERE key = ?", 
                                             (json.dumps(data), key))
                                print(f"  [RESET] Cleared large composer data")
                except Exception as e:
                    print(f"  [ERROR] Could not reset {key}: {e}")
            
            conn.commit()
            print("\n[SUCCESS] Chat data reset!")
            print("\nNext steps:")
            print("  1. Restart Cursor completely")
            print("  2. Try opening the chat again")
    else:
        print("\n[NOT FOUND] No entries with 'Recurring stuck issue' found")
        print("\nThe chat might have been cleared already, or it's stored elsewhere.")
        print("\nTrying to find any large entries that might be causing issues...")
        
        # Find large entries
        cursor.execute("SELECT key, LENGTH(value) as size FROM ItemTable ORDER BY size DESC LIMIT 10")
        large_entries = cursor.fetchall()
        
        print("\nLargest entries in database:")
        for key, size in large_entries:
            print(f"  {key}: {size:,} bytes ({size/1024/1024:.2f} MB)")
            if size > 10 * 1024 * 1024:  # >10MB
                print(f"    [WARNING] This entry is very large and might cause issues!")
    
    conn.close()
    print(f"\n[BACKUP] Your original database is backed up at: {backup_file}")
    print("You can restore it if needed by copying it back to state.vscdb")

if __name__ == "__main__":
    print("=" * 60)
    print("Fix Stuck Chat: Recurring stuck issue")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Backup your database")
    print("  2. Find the corrupted chat entry")
    print("  3. Clear or reset it so you can use Cursor again")
    print("\nYour chat content is already saved in:")
    print("  - recovered_chat_complete.json")
    print("  - recovered_chat_readable.txt")
    print("\n" + "=" * 60)
    
    find_and_fix_stuck_chat()

























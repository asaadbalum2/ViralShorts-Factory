"""
Automatically fix the stuck "Recurring stuck issue" chat
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def auto_fix_stuck_chat():
    """Automatically fix the stuck chat"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup first
    backup_file = storage / f"state.vscdb.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created backup: {backup_file}")
    
    print(f"\nConnecting to database: {db_file}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # Find entries containing "Recurring stuck issue"
    print("\nSearching for 'Recurring stuck issue' entries...")
    cursor.execute("SELECT key, value FROM ItemTable WHERE value LIKE '%Recurring%stuck%issue%' OR value LIKE '%Recurring stuck issue%'")
    matches = cursor.fetchall()
    
    print(f"Found {len(matches)} matching entries")
    
    if not matches:
        print("\n[INFO] No matching entries found. Chat might already be cleared.")
        print("Checking for large entries that might be causing issues...")
        
        cursor.execute("SELECT key, LENGTH(value) as size FROM ItemTable ORDER BY size DESC LIMIT 5")
        large_entries = cursor.fetchall()
        
        if large_entries:
            print("\nLargest entries found:")
            for key, size in large_entries:
                print(f"  {key}: {size/1024/1024:.2f} MB")
                # Clear very large entries (>50MB) that might be corrupted
                if size > 50 * 1024 * 1024:
                    print(f"    [CLEARING] Entry is too large and might be corrupted")
                    cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
        
        conn.commit()
        conn.close()
        return True
    
    print("\n[FOUND] Entries to fix:")
    for key, value in matches:
        try:
            data = json.loads(value)
            if isinstance(data, list):
                print(f"  - {key}: list with {len(data)} items")
            elif isinstance(data, dict):
                print(f"  - {key}: dict with {len(data)} keys")
            else:
                print(f"  - {key}: {type(data)}")
        except:
            print(f"  - {key}: text ({len(value)} chars)")
    
    print("\n" + "=" * 60)
    print("AUTOMATIC FIX: Clearing corrupted chat entries...")
    print("=" * 60)
    
    # Clear the entries
    cleared_count = 0
    for key, value in matches:
        try:
            # For aiService entries, we'll clear them
            # For composer data, we'll try to reset it instead of deleting
            if key == "composer.composerData":
                # Try to reset composer data instead of deleting
                try:
                    data = json.loads(value)
                    if isinstance(data, dict) and 'allComposers' in data:
                        # Clear large composer arrays but keep structure
                        if isinstance(data['allComposers'], list) and len(data['allComposers']) > 10:
                            print(f"  [RESET] {key}: Truncating large composer array")
                            data['allComposers'] = data['allComposers'][-5:]  # Keep last 5
                            cursor.execute("UPDATE ItemTable SET value = ? WHERE key = ?", 
                                         (json.dumps(data), key))
                        else:
                            print(f"  [CLEARED] {key}")
                            cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
                    else:
                        print(f"  [CLEARED] {key}")
                        cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
                except:
                    print(f"  [CLEARED] {key}")
                    cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
            else:
                print(f"  [CLEARED] {key}")
                cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
            cleared_count += 1
        except Exception as e:
            print(f"  [ERROR] Could not clear {key}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Cleared {cleared_count} corrupted entries!")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Close Cursor completely (if it's open)")
    print("2. Restart Cursor")
    print("3. The stuck chat should be gone")
    print("4. Your chat content is saved in:")
    print("   - recovered_chat_complete.json")
    print("   - recovered_chat_readable.txt")
    print("5. If you need the chat content, open those files")
    print("\n[BACKUP] Your original database is backed up at:")
    print(f"   {backup_file}")
    print("   (You can restore it if needed)")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Auto-Fix Stuck Chat: Recurring stuck issue")
    print("=" * 60)
    print("\nThis will automatically:")
    print("  1. Backup your database")
    print("  2. Clear the corrupted chat entries")
    print("  3. Fix the stuck chat issue")
    print("\n" + "=" * 60)
    
    success = auto_fix_stuck_chat()
    
    if success:
        print("\n[COMPLETE] Fix applied! Please restart Cursor now.")
    else:
        print("\n[ERROR] Could not fix the chat. Check the error messages above.")

























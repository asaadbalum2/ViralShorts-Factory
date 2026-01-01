"""
Permanent fix to ensure chat stays available
This script can be run anytime to restore the chat if it gets corrupted
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

# Path to recovered chat data
RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def get_database_path():
    """Get the Cursor database path"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    return storage / "state.vscdb"

def check_chat_exists():
    """Check if chat data exists in database"""
    db_file = get_database_path()
    
    if not db_file.exists():
        return False, "Database not found"
    
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # Check for all three keys
        cursor.execute("SELECT key, LENGTH(value) as size FROM ItemTable WHERE key IN (?, ?, ?)",
                      ('aiService.prompts', 'aiService.generations', 'composer.composerData'))
        rows = cursor.fetchall()
        
        conn.close()
        
        found_keys = {row[0]: row[1] for row in rows}
        
        # Check if all required keys exist and have data
        required_keys = ['aiService.prompts', 'aiService.generations', 'composer.composerData']
        missing = [k for k in required_keys if k not in found_keys or found_keys[k] == 0]
        
        if missing:
            return False, f"Missing or empty keys: {missing}"
        
        # Check if data is reasonable size (should be > 100KB for prompts)
        if found_keys.get('aiService.prompts', 0) < 100 * 1024:
            return False, "Chat data appears corrupted (too small)"
        
        return True, f"Chat exists: prompts={found_keys.get('aiService.prompts', 0)/1024:.1f}KB"
    
    except Exception as e:
        return False, f"Error checking: {e}"

def restore_full_chat():
    """Restore the complete chat conversation"""
    if not RECOVERED_CHAT_FILE.exists():
        return False, "recovered_chat_complete.json not found!"
    
    # Load recovered data
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    db_file = get_database_path()
    
    if not db_file.exists():
        return False, "Database not found"
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    
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
    
    # Restore to database
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    restored = []
    
    if prompts_data is not None:
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('aiService.prompts', json.dumps(prompts_data)))
        restored.append(f"prompts ({len(prompts_data) if isinstance(prompts_data, list) else 'N/A'} items)")
    
    if generations_data is not None:
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('aiService.generations', json.dumps(generations_data)))
        restored.append(f"generations ({len(generations_data) if isinstance(generations_data, list) else 'N/A'} items)")
    
    if composer_data is not None:
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('composer.composerData', json.dumps(composer_data)))
        restored.append("composer data")
    
    conn.commit()
    conn.close()
    
    return True, f"Restored: {', '.join(restored)}"

def main():
    """Main function - check and restore if needed"""
    print("=" * 60)
    print("Permanent Chat Fix: Recurring stuck issue")
    print("=" * 60)
    
    # Check current state
    print("\nChecking chat status...")
    exists, message = check_chat_exists()
    
    if exists:
        print(f"[OK] {message}")
        print("\nChat is available. No action needed.")
        return
    
    print(f"[ISSUE] {message}")
    print("\nRestoring chat...")
    
    # Restore
    success, result = restore_full_chat()
    
    if success:
        print(f"[SUCCESS] {result}")
        print("\n" + "=" * 60)
        print("CHAT RESTORED - Full context available")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Close Cursor completely (if open)")
        print("2. Restart Cursor")
        print("3. Open 'Recurring stuck issue' chat")
        print("4. All messages with full context should be available")
        print("\n[NOTE] If this happens again, just run this script:")
        print("       python permanent_chat_fix.py")
    else:
        print(f"[ERROR] {result}")

if __name__ == "__main__":
    main()























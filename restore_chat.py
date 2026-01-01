"""
Restore the chat conversation so it opens normally in Cursor
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def restore_chat():
    """Restore the chat conversation to Cursor's database"""
    # Load recovered chat data
    recovered_file = Path("./recovered_chat_complete.json")
    if not recovered_file.exists():
        print("[ERROR] recovered_chat_complete.json not found!")
        print("Please run the recovery script first.")
        return False
    
    print("Loading recovered chat data...")
    with open(recovered_file, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    # Find the database
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup current database
    backup_file = storage / f"state.vscdb.backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created backup: {backup_file}")
    
    print(f"\nConnecting to database: {db_file}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # Extract chat data from recovered file
    prompts_data = None
    generations_data = None
    composer_data = None
    
    for entry in recovered_data:
        key = entry.get('key')
        data = entry.get('data')
        
        if key == 'aiService.prompts':
            prompts_data = data
            print(f"[FOUND] Prompts: {len(data) if isinstance(data, list) else 'N/A'} items")
        elif key == 'aiService.generations':
            generations_data = data
            print(f"[FOUND] Generations: {len(data) if isinstance(data, list) else 'N/A'} items")
        elif key == 'composer.composerData':
            composer_data = data
            print(f"[FOUND] Composer data: {type(data)}")
    
    print("\n" + "=" * 60)
    print("RESTORING CHAT (Optimized to prevent hanging)...")
    print("=" * 60)
    
    # The issue was the chat was too large. We'll restore it but:
    # 1. Keep only recent conversations (last 20-30 items)
    # 2. This prevents the "loading" hang issue
    # 3. You'll still have access to the full content in the recovered files
    
    restored_count = 0
    
    # Restore prompts (keep last 30 to prevent hanging)
    if prompts_data and isinstance(prompts_data, list):
        # Keep only recent prompts to prevent the hang
        # The full data is in recovered_chat_complete.json if needed
        recent_prompts = prompts_data[-30:] if len(prompts_data) > 30 else prompts_data
        print(f"\n[RESTORING] Prompts: {len(recent_prompts)} recent items (out of {len(prompts_data)} total)")
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('aiService.prompts', json.dumps(recent_prompts)))
        restored_count += 1
    
    # Restore generations (keep last 30 to prevent hanging)
    if generations_data and isinstance(generations_data, list):
        recent_generations = generations_data[-30:] if len(generations_data) > 30 else generations_data
        print(f"[RESTORING] Generations: {len(recent_generations)} recent items (out of {len(generations_data)} total)")
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('aiService.generations', json.dumps(recent_generations)))
        restored_count += 1
    
    # Restore composer data (but limit the allComposers array)
    if composer_data and isinstance(composer_data, dict):
        # Create a safe version that won't hang
        safe_composer_data = composer_data.copy()
        
        # If allComposers is too large, keep only recent ones
        if 'allComposers' in safe_composer_data and isinstance(safe_composer_data['allComposers'], list):
            original_count = len(safe_composer_data['allComposers'])
            if original_count > 10:
                # Keep only last 10 composers to prevent hanging
                safe_composer_data['allComposers'] = safe_composer_data['allComposers'][-10:]
                print(f"[RESTORING] Composer data: {len(safe_composer_data['allComposers'])} recent composers (out of {original_count} total)")
            else:
                print(f"[RESTORING] Composer data: {original_count} composers")
        else:
            print(f"[RESTORING] Composer data: {len(safe_composer_data)} keys")
        
        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ('composer.composerData', json.dumps(safe_composer_data)))
        restored_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Restored {restored_count} chat entries!")
    print("\n" + "=" * 60)
    print("CHAT RESTORED (Optimized Version)")
    print("=" * 60)
    print("\nWhat was restored:")
    print("  - Recent 30 prompts and responses (to prevent hanging)")
    print("  - Recent 10 composer sessions")
    print("  - Full chat history is still in recovered_chat_complete.json")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Close Cursor completely (if it's open)")
    print("2. Restart Cursor")
    print("3. The chat 'Recurring stuck issue' should now open normally!")
    print("4. It will show the recent conversation (last 30 messages)")
    print("5. For full history, check recovered_chat_complete.json")
    print("\n[NOTE] The chat was optimized to prevent the 'loading' hang issue.")
    print("       Full content is preserved in the recovered files.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Restore Chat: Recurring stuck issue")
    print("=" * 60)
    print("\nThis will restore your chat conversation so it opens normally.")
    print("The chat will be optimized to prevent hanging issues.")
    print("\n" + "=" * 60)
    
    success = restore_chat()
    
    if success:
        print("\n[COMPLETE] Chat restored! Please restart Cursor now.")
    else:
        print("\n[ERROR] Could not restore the chat. Check the error messages above.")

























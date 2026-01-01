"""
Deep investigation - why the chat won't open
"""
import os
import sqlite3
import json
from pathlib import Path

def investigate():
    """Investigate why chat won't open"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DEEP INVESTIGATION - Why Chat Won't Open")
    print("=" * 60)
    
    # 1. Check composer data structure
    print("\n1. Checking composer data structure...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        composer_data = json.loads(row[0])
        all_composers = composer_data.get('allComposers', [])
        
        # Find the recurring chat
        for composer in all_composers:
            if not isinstance(composer, dict):
                continue
            composer_id = composer.get('id') or composer.get('composerId')
            if composer_id == 'd08a3fb1-967f-4ba7-b242-fa8bda453bf5':
                print(f"\n   Found 'Recurring stuck issue' chat:")
                print(f"   ID: {composer_id}")
                print(f"   Keys in composer object: {list(composer.keys())}")
                
                # Check important fields
                for key in ['title', 'name', 'label', 'createdAt', 'updatedAt', 'messages', 'conversationId']:
                    if key in composer:
                        value = composer[key]
                        if isinstance(value, (list, dict)):
                            print(f"   {key}: {type(value).__name__} with {len(value)} items")
                        else:
                            print(f"   {key}: {value}")
    
    # 2. Check for chat session files
    print("\n2. Checking for chat session files...")
    storage = db_file.parent
    chat_sessions_dir = storage / "chatSessions"
    if chat_sessions_dir.exists():
        print(f"   Found chatSessions directory")
        for session_file in chat_sessions_dir.iterdir():
            if session_file.is_file():
                print(f"   Session file: {session_file.name}")
                try:
                    with open(session_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(500)  # First 500 chars
                        if 'recurring' in content.lower() or 'stuck' in content.lower():
                            print(f"      [MATCH] This might be the recurring chat session")
                except:
                    pass
    
    # 3. Check all chat-related keys
    print("\n3. Checking all chat-related database keys...")
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%composer%' OR key LIKE '%conversation%' OR key LIKE '%aichat%'")
    keys = cursor.fetchall()
    print(f"   Found {len(keys)} chat-related keys")
    for (key,) in keys[:20]:  # Show first 20
        print(f"      - {key}")
    
    # 4. Check if there's a specific key for the chat ID
    print("\n4. Checking for chat-specific state keys...")
    chat_id = 'd08a3fb1-967f-4ba7-b242-fa8bda453bf5'
    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE ? OR value LIKE ?",
                  (f'%{chat_id}%', f'%{chat_id}%'))
    matching_keys = cursor.fetchall()
    if matching_keys:
        print(f"   Found {len(matching_keys)} keys containing chat ID:")
        for key, value in matching_keys[:10]:
            print(f"      - {key}: {str(value)[:100]}...")
    
    # 5. Check workbench panel keys (UI state)
    print("\n5. Checking workbench panel keys (UI state)...")
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE 'workbench.panel.aichat%'")
    panel_keys = cursor.fetchall()
    print(f"   Found {len(panel_keys)} panel state keys")
    for (key,) in panel_keys[:5]:
        cursor.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                value = json.loads(row[0])
                print(f"      {key}: {value}")
            except:
                print(f"      {key}: {str(row[0])[:50]}...")
    
    # 6. Check if chat needs to be in a different location
    print("\n6. Checking for alternative chat storage...")
    global_storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "globalStorage"
    if global_storage.exists():
        print(f"   Global storage exists: {global_storage}")
        # Check for chat-related files
        for item in global_storage.iterdir():
            if 'chat' in item.name.lower() or 'composer' in item.name.lower():
                print(f"      Found: {item.name}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("INVESTIGATION COMPLETE")
    print("=" * 60)
    print("\nBased on this investigation, the issue might be:")
    print("  - Chat session file missing or corrupted")
    print("  - UI state not properly set")
    print("  - Chat needs to be in a different format")
    print("\nNext: Will try to create a fresh chat session with the data")

if __name__ == "__main__":
    investigate()





















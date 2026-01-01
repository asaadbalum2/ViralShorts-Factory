"""
Extract the full chat from the database
"""
import os
import sqlite3
import json
from pathlib import Path

def extract_full_chat():
    """Extract the complete chat from ItemTable"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    print(f"Extracting chat from: {db_file}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # Get all rows containing "Recurring" or "stuck"
    cursor.execute("SELECT key, value FROM ItemTable WHERE value LIKE '%Recurring%' OR value LIKE '%stuck issue%'")
    matches = cursor.fetchall()
    
    print(f"Found {len(matches)} matching entries")
    
    all_chats = []
    for key, value in matches:
        try:
            # Try to parse as JSON
            data = json.loads(value)
            all_chats.append({
                'key': key,
                'data': data
            })
            print(f"\n[FOUND] Key: {key}")
            print(f"  Type: {type(data)}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
        except:
            # Not JSON, save as text
            all_chats.append({
                'key': key,
                'data': value
            })
            print(f"\n[FOUND] Key: {key} (text data, {len(value)} chars)")
    
    # Save all found chats
    if all_chats:
        output = Path("./recovered_chat_complete.json")
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(all_chats, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVED] Complete chat saved to: {output}")
        
        # Also try to extract readable messages
        print("\n" + "=" * 60)
        print("Extracting readable messages...")
        messages = []
        for chat in all_chats:
            data = chat['data']
            if isinstance(data, dict):
                # Look for message-like structures
                if 'messages' in data:
                    messages.extend(data['messages'])
                elif 'conversation' in data:
                    messages.extend(data['conversation'])
                elif 'chat' in data:
                    messages.extend(data['chat'])
                # Also check if the whole thing is a message array
                elif isinstance(data, list):
                    messages.extend(data)
        
        if messages:
            output_messages = Path("./recovered_chat_messages.json")
            with open(output_messages, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            print(f"[SAVED] Messages saved to: {output_messages}")
        
        # Also create a readable text version
        output_text = Path("./recovered_chat_readable.txt")
        with open(output_text, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("RECOVERED CHAT: Recurring stuck issue\n")
            f.write("=" * 60 + "\n\n")
            for chat in all_chats:
                f.write(f"\n--- Key: {chat['key']} ---\n\n")
                data = chat['data']
                if isinstance(data, dict):
                    f.write(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    f.write(str(data))
                f.write("\n\n")
        print(f"[SAVED] Readable text saved to: {output_text}")
        
        return all_chats
    
    conn.close()
    return None

if __name__ == "__main__":
    extract_full_chat()


























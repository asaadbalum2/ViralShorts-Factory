"""
Force read chat sessions - try multiple methods
"""
import os
import json
import shutil
from pathlib import Path

def force_read_file(file_path):
    """Try multiple methods to read a file"""
    methods = [
        lambda f: open(f, 'r', encoding='utf-8').read(),
        lambda f: open(f, 'rb').read().decode('utf-8', errors='ignore'),
    ]
    
    for method in methods:
        try:
            return method(file_path)
        except:
            continue
    return None

def search_all_chats():
    """Search all possible chat locations"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage"
    
    results = []
    
    print("Searching for 'Recurring stuck issue' chat...")
    print("=" * 60)
    
    # Search all workspace directories
    for workspace_dir in storage.iterdir():
        if not workspace_dir.is_dir():
            continue
        
        # Check chatSessions
        chat_sessions = workspace_dir / "chatSessions"
        if chat_sessions.exists():
            for session_file in chat_sessions.iterdir():
                if session_file.is_file() and session_file.suffix == '.json':
                    try:
                        content = force_read_file(session_file)
                        if content and ("Recurring" in content or "stuck issue" in content.lower()):
                            print(f"\n[FOUND] {session_file}")
                            results.append((session_file, content))
                    except:
                        pass
        
        # Check chatEditingSessions
        chat_editing = workspace_dir / "chatEditingSessions"
        if chat_editing.exists():
            for session_file in chat_editing.iterdir():
                if session_file.is_file() and session_file.suffix == '.json':
                    try:
                        content = force_read_file(session_file)
                        if content and ("Recurring" in content or "stuck issue" in content.lower()):
                            print(f"\n[FOUND] {session_file}")
                            results.append((session_file, content))
                    except:
                        pass
        
        # Check all JSON files in workspace
        for json_file in workspace_dir.rglob("*.json"):
            try:
                content = force_read_file(json_file)
                if content and "Recurring stuck issue" in content:
                    print(f"\n[FOUND] {json_file}")
                    results.append((json_file, content))
            except:
                pass
    
    # Also check backup
    backup_dir = Path("./cursor_chat_backup/20251225_165600")
    if backup_dir.exists():
        print("\nChecking backup files...")
        for json_file in backup_dir.rglob("*.json"):
            try:
                content = force_read_file(json_file)
                if content and ("Recurring" in content or "stuck issue" in content.lower()):
                    print(f"\n[FOUND IN BACKUP] {json_file}")
                    results.append((json_file, content))
            except:
                pass
    
    # Save all found chats
    if results:
        print(f"\n[SUCCESS] Found {len(results)} matching chat(s)")
        for i, (file_path, content) in enumerate(results, 1):
            try:
                # Try to parse as JSON
                data = json.loads(content)
                output = Path(f"./recovered_chat_{i}.json")
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  [SAVED] {output}")
            except:
                # Save as text
                output = Path(f"./recovered_chat_{i}.txt")
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  [SAVED] {output}")
        
        return results[0][1]  # Return first chat content
    else:
        print("\n[NOT FOUND] Could not find the chat")
        print("\nTrying to list all chat sessions...")
        # List all chat sessions
        for workspace_dir in storage.iterdir():
            if not workspace_dir.is_dir():
                continue
            chat_sessions = workspace_dir / "chatSessions"
            if chat_sessions.exists():
                print(f"\nChat sessions in {workspace_dir.name}:")
                for session_file in chat_sessions.iterdir():
                    if session_file.is_file():
                        print(f"  - {session_file.name}")
                        # Try to read first few lines
                        try:
                            content = force_read_file(session_file)
                            if content:
                                # Look for title/name in first 500 chars
                                preview = content[:500]
                                if "title" in preview.lower() or "name" in preview.lower():
                                    print(f"    Preview: {preview[:100]}...")
                        except:
                            pass
        return None

if __name__ == "__main__":
    search_all_chats()


























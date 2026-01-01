"""
Find Cursor chat (not GitHub Copilot)
"""
import os
import json
from pathlib import Path

def find_cursor_chats():
    """Find actual Cursor chat sessions"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage"
    
    # Also check globalStorage
    global_storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "globalStorage"
    
    locations = [
        storage,
        global_storage,
    ]
    
    print("Searching for Cursor chat sessions...")
    print("=" * 60)
    
    all_chats = []
    
    for base_path in locations:
        if not base_path.exists():
            continue
            
        print(f"\nSearching: {base_path}")
        
        # Look for any JSON files that might contain chat data
        for json_file in base_path.rglob("*.json"):
            try:
                # Skip very large files initially
                if json_file.stat().st_size > 50 * 1024 * 1024:  # >50MB
                    continue
                    
                with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first 10KB to check
                    preview = f.read(10000)
                    f.seek(0)
                    
                    # Look for Cursor-specific patterns
                    if "cursor" in preview.lower() or "chat" in preview.lower():
                        # Check if it contains "Recurring" or "stuck"
                        full_content = f.read()
                        if "Recurring" in full_content or "stuck issue" in full_content.lower():
                            print(f"\n[FOUND MATCH] {json_file}")
                            all_chats.append((json_file, full_content))
                            # Save it immediately
                            try:
                                data = json.loads(full_content)
                                output = Path("./recovered_chat.json")
                                with open(output, 'w', encoding='utf-8') as out:
                                    json.dump(data, out, indent=2, ensure_ascii=False)
                                print(f"  [SAVED] {output}")
                            except:
                                output = Path("./recovered_chat.txt")
                                with open(output, 'w', encoding='utf-8') as out:
                                    out.write(full_content)
                                print(f"  [SAVED] {output}")
            except Exception as e:
                pass
    
    # Also check for SQLite databases (Cursor might use them)
    for base_path in locations:
        if not base_path.exists():
            continue
        for db_file in base_path.rglob("*.db"):
            print(f"\n[FOUND DB] {db_file} (might contain chat history)")
    
    # List all workspace folders to help identify
    print("\n" + "=" * 60)
    print("Workspace folders found:")
    if storage.exists():
        for workspace_dir in storage.iterdir():
            if workspace_dir.is_dir():
                workspace_json = workspace_dir / "workspace.json"
                if workspace_json.exists():
                    try:
                        with open(workspace_json, 'r', encoding='utf-8') as f:
                            ws_data = json.load(f)
                            folder = ws_data.get('folder', 'Unknown')
                            print(f"  {workspace_dir.name}: {folder}")
                    except:
                        print(f"  {workspace_dir.name}: (could not read)")
    
    return all_chats

if __name__ == "__main__":
    find_cursor_chats()


























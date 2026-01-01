"""
Directly read chat session files (even if locked)
"""
import os
import json
from pathlib import Path

def read_chat_sessions():
    """Try to read chat session files directly"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage"
    
    if not storage.exists():
        print("Storage not found")
        return
    
    print(f"Searching in: {storage}")
    print("=" * 60)
    
    # Look for chatSessions folders
    for workspace_dir in storage.iterdir():
        if not workspace_dir.is_dir():
            continue
            
        chat_sessions = workspace_dir / "chatSessions"
        chat_editing = workspace_dir / "chatEditingSessions"
        
        if chat_sessions.exists():
            print(f"\n[FOUND] chatSessions in: {workspace_dir.name}")
            try:
                for session_file in chat_sessions.rglob("*"):
                    if session_file.is_file():
                        try:
                            # Try to read even if locked
                            with open(session_file, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if "Recurring" in content or "stuck" in content.lower():
                                    print(f"  [MATCH] {session_file.name}")
                                    # Try to parse
                                    try:
                                        data = json.loads(content)
                                        # Save it
                                        output = Path("./recovered_chat.json")
                                        with open(output, 'w', encoding='utf-8') as out:
                                            json.dump(data, out, indent=2, ensure_ascii=False)
                                        print(f"  [SAVED] Chat saved to: {output}")
                                        return output
                                    except:
                                        # Save as text
                                        output = Path("./recovered_chat.txt")
                                        with open(output, 'w', encoding='utf-8') as out:
                                            out.write(content)
                                        print(f"  [SAVED] Chat saved to: {output}")
                                        return output
                        except PermissionError:
                            print(f"  [LOCKED] {session_file.name} (Cursor is using it)")
                        except Exception as e:
                            pass
            except Exception as e:
                print(f"  Error: {e}")
        
        if chat_editing.exists():
            print(f"\n[FOUND] chatEditingSessions in: {workspace_dir.name}")
            try:
                for session_file in chat_editing.rglob("*"):
                    if session_file.is_file():
                        try:
                            with open(session_file, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if "Recurring" in content or "stuck" in content.lower():
                                    print(f"  [MATCH] {session_file.name}")
                                    try:
                                        data = json.loads(content)
                                        output = Path("./recovered_chat.json")
                                        with open(output, 'w', encoding='utf-8') as out:
                                            json.dump(data, out, indent=2, ensure_ascii=False)
                                        print(f"  [SAVED] Chat saved to: {output}")
                                        return output
                                    except:
                                        output = Path("./recovered_chat.txt")
                                        with open(output, 'w', encoding='utf-8') as out:
                                            out.write(content)
                                        print(f"  [SAVED] Chat saved to: {output}")
                                        return output
                        except PermissionError:
                            print(f"  [LOCKED] {session_file.name}")
                        except Exception as e:
                            pass
            except Exception as e:
                print(f"  Error: {e}")
    
    print("\n[INFO] Searching all JSON files for chat content...")
    # Also search all JSON files
    for workspace_dir in storage.iterdir():
        if not workspace_dir.is_dir():
            continue
        for json_file in workspace_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "Recurring stuck issue" in content:
                        print(f"\n[FOUND MATCH] {json_file}")
                        try:
                            data = json.loads(content)
                            output = Path("./recovered_chat.json")
                            with open(output, 'w', encoding='utf-8') as out:
                                json.dump(data, out, indent=2, ensure_ascii=False)
                            print(f"[SAVED] Chat saved to: {output}")
                            return output
                        except:
                            output = Path("./recovered_chat.txt")
                            with open(output, 'w', encoding='utf-8') as out:
                                out.write(content)
                            print(f"[SAVED] Chat saved to: {output}")
                            return output
            except:
                pass

if __name__ == "__main__":
    read_chat_sessions()


























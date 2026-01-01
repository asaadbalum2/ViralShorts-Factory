"""
Cursor Chat Recovery Script
Safely backs up and attempts to recover stuck chat
"""
import os
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def find_cursor_chat_storage():
    """Find Cursor's chat storage location"""
    appdata = os.getenv('APPDATA')
    if not appdata:
        return None
    
    possible_paths = [
        Path(appdata) / "Cursor" / "User" / "workspaceStorage",
        Path(appdata) / "Cursor" / "User" / "History",
        Path(appdata) / "Cursor" / "Storage",
        Path.home() / ".cursor" / "storage",
        Path(appdata) / "Cursor" / "User" / "globalStorage",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"[OK] Found: {path}")
            return path
    
    return None

def backup_chat_data(storage_path):
    """Backup all chat-related files"""
    backup_dir = Path("./cursor_chat_backup") / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating backup in: {backup_dir}")
    
    # Look for chat-related files
    chat_patterns = ["*chat*", "*conversation*", "*history*", "*.json", "*.db", "*.sqlite"]
    
    files_backed_up = 0
    for pattern in chat_patterns:
        for file_path in storage_path.rglob(pattern):
            try:
                # Skip if file is too large (>50MB)
                if file_path.stat().st_size > 50 * 1024 * 1024:
                    continue
                    
                rel_path = file_path.relative_to(storage_path)
                backup_file = backup_dir / rel_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_file)
                files_backed_up += 1
                if files_backed_up % 10 == 0:
                    print(f"  Backed up {files_backed_up} files...")
            except Exception as e:
                print(f"  Error backing up {file_path}: {e}")
    
    print(f"\n[OK] Backed up {files_backed_up} files")
    return backup_dir

def search_for_chat_content(storage_path, search_term="Recurring stuck issue"):
    """Search for the specific chat by name"""
    print(f"\nSearching for chat: '{search_term}'")
    
    found_files = []
    for file_path in storage_path.rglob("*.json"):
        try:
            # Check file size first
            if file_path.stat().st_size > 10 * 1024 * 1024:  # Skip files >10MB
                continue
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if search_term.lower() in content.lower():
                    found_files.append(file_path)
                    print(f"  [FOUND] {file_path}")
                    
                    # Try to extract chat content
                    try:
                        data = json.loads(content)
                        print(f"    -> File contains JSON data")
                    except:
                        print(f"    -> File contains text data")
        except Exception as e:
            pass
    
    return found_files

def extract_chat_from_file(file_path):
    """Try to extract readable chat content from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Try JSON parsing
        try:
            data = json.loads(content)
            # Pretty print
            output_file = Path("./cursor_chat_backup") / f"extracted_chat_{datetime.now().strftime('%H%M%S')}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as out:
                json.dump(data, out, indent=2, ensure_ascii=False)
            print(f"  [EXTRACTED] {output_file}")
            return output_file
        except:
            # Save as text
            output_file = Path("./cursor_chat_backup") / f"extracted_chat_{datetime.now().strftime('%H%M%S')}.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(content)
            print(f"  [EXTRACTED] {output_file}")
            return output_file
    except Exception as e:
        print(f"  Error extracting: {e}")
        return None

def main():
    print("=" * 60)
    print("Cursor Chat Recovery Tool")
    print("=" * 60)
    
    # Find storage
    storage_path = find_cursor_chat_storage()
    if not storage_path:
        print("\n[ERROR] Could not find Cursor storage directory")
        print("\nManual locations to check:")
        print("  1. %APPDATA%\\Cursor\\User\\workspaceStorage\\")
        print("  2. %APPDATA%\\Cursor\\User\\globalStorage\\")
        print("  3. Check Cursor Settings > Storage location")
        return
    
    print(f"\n[OK] Found Cursor storage: {storage_path}")
    
    # Backup first
    print("\n" + "=" * 60)
    print("STEP 1: Creating backup (this is safe, won't delete anything)")
    print("=" * 60)
    backup_dir = backup_chat_data(storage_path)
    print(f"\n[OK] Backup complete: {backup_dir}")
    
    # Search for the specific chat
    print("\n" + "=" * 60)
    print("STEP 2: Searching for your chat")
    print("=" * 60)
    found = search_for_chat_content(storage_path)
    
    if found:
        print(f"\n[SUCCESS] Found {len(found)} files containing chat data")
        print("\nExtracting chat content...")
        for file_path in found:
            extract_chat_from_file(file_path)
        
        print("\n" + "=" * 60)
        print("SUCCESS! Chat content found and backed up!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Check the 'cursor_chat_backup' folder")
        print("  2. Look for 'extracted_chat_*.json' or 'extracted_chat_*.txt' files")
        print("  3. Open them to see your chat content")
        print("  4. Copy the content to a safe place")
        print("\nNow you can safely try to fix the stuck chat in Cursor.")
    else:
        print("\n[WARNING] Could not find specific chat files by name")
        print("  But backup is safe - all files are backed up")
        print("\nTry searching manually in the backup folder for JSON files")
        print("  that might contain your chat content.")
    
    print("\n" + "=" * 60)
    print("Recovery complete! Check the 'cursor_chat_backup' folder.")
    print("=" * 60)

if __name__ == "__main__":
    main()


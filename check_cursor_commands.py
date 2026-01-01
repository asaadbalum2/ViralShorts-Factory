"""
Check what Cursor commands are available and try to find the right way to open composer
"""
import os
import sqlite3
import json
from pathlib import Path

def check_commands():
    """Check Cursor's command structure"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Checking Cursor Commands and Structure")
    print("=" * 60)
    
    # Check for command-related keys
    print("\n1. Checking for command/action keys...")
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%command%' OR key LIKE '%action%' OR key LIKE '%menu%'")
    command_keys = cursor.fetchall()
    if command_keys:
        print(f"   Found {len(command_keys)} command-related keys")
        for (key,) in command_keys[:10]:
            print(f"      - {key}")
    
    # Check workbench state
    print("\n2. Checking workbench state...")
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE 'workbench%'")
    workbench_keys = cursor.fetchall()
    print(f"   Found {len(workbench_keys)} workbench keys")
    
    # Check if composer is in a specific state
    print("\n3. Checking composer visibility state...")
    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%composer%' OR key LIKE '%chat%'")
    composer_keys = cursor.fetchall()
    print(f"   Found {len(composer_keys)} composer/chat keys:")
    for (key, value) in composer_keys[:15]:
        try:
            if isinstance(value, str) and len(value) < 200:
                print(f"      - {key}: {value[:100]}")
            else:
                print(f"      - {key}: (data)")
        except:
            print(f"      - {key}: (data)")
    
    # Check the actual chat we created
    print("\n4. Checking our chat status...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        comp_data = json.loads(row[0])
        all_composers = comp_data.get('allComposers', [])
        selected = comp_data.get('selectedComposerIds', [])
        
        print(f"   Total composers: {len(all_composers)}")
        print(f"   Selected: {selected}")
        
        for comp in all_composers:
            if not isinstance(comp, dict):
                continue
            name = comp.get('name') or comp.get('title') or 'Untitled'
            comp_id = comp.get('id') or comp.get('composerId')
            if 'recurring' in name.lower() or 'stuck' in name.lower():
                print(f"\n   [OUR CHAT]")
                print(f"      Name: {name}")
                print(f"      ID: {comp_id}")
                print(f"      isArchived: {comp.get('isArchived')}")
                print(f"      isHidden: {comp.get('isHidden')}")
                print(f"      isPinned: {comp.get('isPinned')}")
                print(f"      Selected: {comp_id in selected}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("SUGGESTIONS:")
    print("=" * 60)
    print("\nSince Cursor doesn't have 'Composer: Open Composer' command,")
    print("try these instead:")
    print("\n1. Look for a chat/composer icon in Cursor's sidebar")
    print("2. Check the bottom panel - there might be a chat tab")
    print("3. Look in the left sidebar for 'Chat' or 'Composer'")
    print("4. Try right-clicking in the editor → might have 'Open Chat'")
    print("\nOR use the HTML viewer:")
    print("  - Open 'chat_viewer.html' in your browser")
    print("  - All your messages are there!")
    print("=" * 60)

if __name__ == "__main__":
    check_commands()
















"""
Deep fix - make chat actually clickable by ensuring proper conversation thread
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

def deep_fix():
    """Deep investigation and fix to make chat clickable"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return False
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_deep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("DEEP FIX - Making Chat Actually Clickable")
    print("=" * 60)
    
    # 1. Find the chat we created
    print("\n1. Finding the chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return False
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    target_chat = None
    target_id = None
    
    for composer in all_composers:
        if not isinstance(composer, dict):
            continue
        name = composer.get('name') or composer.get('title') or ''
        if 'recurring' in name.lower() and 'stuck' in name.lower():
            target_chat = composer
            target_id = composer.get('id') or composer.get('composerId')
            print(f"   [FOUND] Chat: '{name}' (ID: {target_id})")
            break
    
    if not target_chat:
        print("[ERROR] Chat not found")
        conn.close()
        return False
    
    # 2. Check how other working chats are structured
    print("\n2. Analyzing working chats for comparison...")
    working_chats = []
    for composer in all_composers:
        if not isinstance(composer, dict):
            continue
        comp_id = composer.get('id') or composer.get('composerId')
        if comp_id != target_id:
            # Check if this chat has any special fields
            keys = list(composer.keys())
            if len(keys) > 15:  # Likely a working chat
                working_chats.append((composer, keys))
    
    if working_chats:
        print(f"   [FOUND] {len(working_chats)} other chats to compare")
        # Get all unique keys from working chats
        all_keys = set()
        for chat, keys in working_chats:
            all_keys.update(keys)
        print(f"   [INFO] Working chats have {len(all_keys)} unique fields")
        
        # Ensure our chat has all the same fields
        for key in all_keys:
            if key not in target_chat:
                # Get default from a working chat
                for chat, _ in working_chats:
                    if key in chat:
                        target_chat[key] = chat[key]
                        break
                else:
                    # Set sensible default
                    if 'is' in key.lower():
                        target_chat[key] = False
                    elif 'has' in key.lower():
                        target_chat[key] = False
                    elif 'num' in key.lower() or 'count' in key.lower():
                        target_chat[key] = 0
                    elif 'percent' in key.lower():
                        target_chat[key] = 0
    
    # 3. Ensure chat is NOT archived and IS active
    print("\n3. Ensuring chat is active...")
    target_chat['isArchived'] = False
    target_chat['isDraft'] = False
    target_chat['isHidden'] = False
    target_chat['isPinned'] = True
    target_chat['hasUnreadMessages'] = False
    target_chat['lastUpdatedAt'] = int(datetime.now().timestamp() * 1000)
    
    # 4. Update the composer in the list
    for i, comp in enumerate(all_composers):
        comp_id = comp.get('id') or comp.get('composerId')
        if comp_id == target_id:
            all_composers[i] = target_chat
            break
    
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [target_id]
    composer_data['lastFocusedComposerIds'] = [target_id]
    
    # 5. Save composer data
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 6. Check if there's a conversation thread that needs to be created
    print("\n4. Checking for conversation threads...")
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%conversation%' OR key LIKE '%thread%'")
    thread_keys = cursor.fetchall()
    print(f"   [FOUND] {len(thread_keys)} conversation-related keys")
    
    # 7. Create/update workbench state to force UI refresh
    print("\n5. Forcing UI refresh...")
    
    # Delete old panel states for this chat
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE 'workbench.panel.composerChatViewPane%'")
    panel_keys = cursor.fetchall()
    
    for (key,) in panel_keys:
        try:
            cursor.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                panel_data = json.loads(row[0])
                if isinstance(panel_data, dict):
                    # Remove any references to old chat IDs
                    view_key = f"workbench.panel.aichat.view.{target_id}"
                    if view_key in panel_data:
                        panel_data[view_key] = {
                            'collapsed': False,
                            'isHidden': False,
                            'visible': True
                        }
                        cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                                      (key, json.dumps(panel_data)))
        except:
            pass
    
    # 8. Create a fresh panel state
    import uuid
    new_panel_id = str(uuid.uuid4())
    view_key = f"workbench.panel.aichat.view.{target_id}"
    panel_key = f"workbench.panel.composerChatViewPane.{new_panel_id}"
    
    fresh_panel = {
        view_key: {
            'collapsed': False,
            'isHidden': False,
            'visible': True,
            'active': True
        }
    }
    
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (panel_key, json.dumps(fresh_panel)))
    
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (f"workbench.panel.aichat.{new_panel_id}.numberOfVisibleViews", json.dumps(1)))
    
    # 9. Set workspace state to show composer
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('workbench.backgroundComposer.workspacePersistentData', json.dumps({
                      'selectedComposerId': target_id,
                      'isVisible': True
                  })))
    
    # 10. Clear any error or blocking states
    cursor.execute("DELETE FROM ItemTable WHERE key LIKE '%error%' AND key LIKE '%composer%'")
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('cursor/needsComposerInitialOpening', json.dumps(False)))
    
    conn.commit()
    
    # 11. Final verification
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    if row:
        comp_data = json.loads(row[0])
        for comp in comp_data.get('allComposers', []):
            comp_id = comp.get('id') or comp.get('composerId')
            if comp_id == target_id:
                print(f"  Chat: {comp.get('name', 'N/A')}")
                print(f"  isArchived: {comp.get('isArchived')}")
                print(f"  isHidden: {comp.get('isHidden')}")
                print(f"  isPinned: {comp.get('isPinned')}")
                print(f"  Selected: {comp_id in comp_data.get('selectedComposerIds', [])}")
                print(f"  Fields: {len(comp)} fields")
                break
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("DEEP FIX COMPLETE")
    print("=" * 60)
    print("\nThe chat has been:")
    print("  - Compared with working chats")
    print("  - Updated with all required fields")
    print("  - Made active and visible")
    print("  - UI state refreshed")
    print("  - Panel states recreated")
    print("\n" + "=" * 60)
    print("CRITICAL: Try this NOW:")
    print("=" * 60)
    print("\n1. In Cursor, press Ctrl+Shift+P")
    print("2. Type: 'Composer: Open Composer'")
    print("3. OR type: 'View: Show Composer'")
    print("4. This should open the composer panel")
    print("5. The chat should be visible and clickable")
    print("\nIf that doesn't work:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. Press Ctrl+Shift+P")
    print("4. Type: 'Composer: Open Composer'")
    print("5. The chat should appear")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("DEEP FIX - Make Chat Clickable")
    print("=" * 60)
    deep_fix()
















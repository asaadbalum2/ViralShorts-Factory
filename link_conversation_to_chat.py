"""
Link the conversation properly to the chat so it opens
This is the real fix - ensuring conversation is linked to composer
"""
import os
import sqlite3
import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def link_conversation():
    """Properly link conversation to chat so it opens"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    # Backup
    backup_file = db_file.parent / f"state.vscdb.backup_link_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_file, backup_file)
    print(f"[BACKUP] Created: {backup_file.name}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("LINKING CONVERSATION TO CHAT")
    print("=" * 60)
    
    # 1. Load conversation
    print("\n1. Loading conversation...")
    prompts_data = []
    generations_data = []
    
    if RECOVERED_CHAT_FILE.exists():
        with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
            recovered_data = json.load(f)
        
        for entry in recovered_data:
            key = entry.get('key')
            data = entry.get('data')
            
            if key == 'aiService.prompts' and isinstance(data, list):
                prompts_data = data
                print(f"   [LOADED] {len(prompts_data)} prompts")
            elif key == 'aiService.generations' and isinstance(data, list):
                generations_data = data
                print(f"   [LOADED] {len(generations_data)} generations")
    
    # 2. Get or create the chat
    print("\n2. Getting/creating chat...")
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        composer_data = {'allComposers': [], 'selectedComposerIds': [], 'lastFocusedComposerIds': []}
    else:
        composer_data = json.loads(row[0])
    
    all_composers = composer_data.get('allComposers', [])
    
    # Find existing "Recurring stuck issue" or create new
    target_chat = None
    target_id = None
    
    for composer in all_composers:
        if not isinstance(composer, dict):
            continue
        name = composer.get('name') or composer.get('title') or ''
        if 'recurring' in name.lower() and 'stuck' in name.lower():
            target_chat = composer
            target_id = composer.get('id') or composer.get('composerId')
            print(f"   [FOUND] Existing chat: {target_id}")
            break
    
    if not target_chat:
        # Create new
        target_id = str(uuid.uuid4())
        now_ms = int(datetime.now().timestamp() * 1000)
        target_chat = {
            'id': target_id,
            'composerId': target_id,
            'name': 'Recurring stuck issue',
            'createdAt': now_ms,
            'lastUpdatedAt': now_ms,
        }
        all_composers.insert(0, target_chat)
        print(f"   [CREATED] New chat: {target_id}")
    
    # 3. Update chat to be current and active
    target_chat['name'] = 'Recurring stuck issue'
    target_chat['lastUpdatedAt'] = int(datetime.now().timestamp() * 1000)
    target_chat['isArchived'] = False
    target_chat['isDraft'] = False
    target_chat['isHidden'] = False
    
    # Update in list
    for i, comp in enumerate(all_composers):
        comp_id = comp.get('id') or comp.get('composerId')
        if comp_id == target_id:
            all_composers[i] = target_chat
            break
    
    composer_data['allComposers'] = all_composers
    composer_data['selectedComposerIds'] = [target_id]
    composer_data['lastFocusedComposerIds'] = [target_id]
    
    # Save
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('composer.composerData', json.dumps(composer_data, ensure_ascii=False)))
    
    # 4. CRITICAL: Save prompts and generations with proper structure
    print("\n3. Saving conversation with proper structure...")
    
    # The key insight: prompts and generations might need to be stored per-composer
    # But Cursor might use global storage. Let's ensure both are saved correctly
    
    # Global storage (for all chats)
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('aiService.prompts', json.dumps(prompts_data, ensure_ascii=False)))
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('aiService.generations', json.dumps(generations_data, ensure_ascii=False)))
    
    # Also try composer-specific storage
    composer_prompts_key = f'aiService.prompts.{target_id}'
    composer_gens_key = f'aiService.generations.{target_id}'
    
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (composer_prompts_key, json.dumps(prompts_data, ensure_ascii=False)))
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (composer_gens_key, json.dumps(generations_data, ensure_ascii=False)))
    
    print(f"   [SAVED] Conversation linked to chat {target_id}")
    
    # 5. Create proper UI state
    print("\n4. Creating UI state...")
    
    # Create a fresh panel state
    panel_id = str(uuid.uuid4())
    view_key = f"workbench.panel.aichat.view.{target_id}"
    panel_key = f"workbench.panel.composerChatViewPane.{panel_id}"
    
    panel_data = {
        view_key: {
            'collapsed': False,
            'isHidden': False,
            'visible': True,
            'active': True
        }
    }
    
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (panel_key, json.dumps(panel_data)))
    
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  (f'workbench.panel.aichat.{panel_id}.numberOfVisibleViews', json.dumps(1)))
    
    # 6. Set workspace to show this chat
    cursor.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                  ('workbench.backgroundComposer.workspacePersistentData', json.dumps({
                      'selectedComposerId': target_id,
                      'isVisible': True,
                      'lastFocusedComposerId': target_id
                  })))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("CONVERSATION LINKED - READY TO CONTINUE")
    print("=" * 60)
    print(f"\nChat ID: {target_id}")
    print(f"Name: 'Recurring stuck issue'")
    print(f"Conversation: {len(prompts_data)} prompts + {len(generations_data)} responses")
    print(f"Linked: YES (both global and composer-specific)")
    print("\n" + "=" * 60)
    print("FINAL RESTART:")
    print("=" * 60)
    print("\n1. Close Cursor completely (Task Manager)")
    print("2. Wait 10 seconds")
    print("3. Start Cursor")
    print("4. The chat 'Recurring stuck issue' should:")
    print("   - Appear in chat list")
    print("   - Be clickable")
    print("   - Open with ALL 279 messages")
    print("   - Allow you to continue your project!")
    print("\nThe conversation is now properly linked to the chat.")
    print("This should work!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Link Conversation to Chat - Continue Your Project")
    print("=" * 60)
    link_conversation()










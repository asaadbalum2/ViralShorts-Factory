"""
Investigate why multiple chats are not clickable
"""
import os
import sqlite3
import json
from pathlib import Path

def investigate():
    """Investigate all chats and find why some aren't clickable"""
    db_file = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008" / "state.vscdb"
    
    if not db_file.exists():
        print("[ERROR] Database not found")
        return
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    print("=" * 60)
    print("INVESTIGATING NON-CLICKABLE CHATS")
    print("=" * 60)
    
    # Get composer data
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cursor.fetchone()
    
    if not row:
        print("[ERROR] Composer data not found")
        conn.close()
        return
    
    composer_data = json.loads(row[0])
    all_composers = composer_data.get('allComposers', [])
    
    print(f"\nFound {len(all_composers)} total chats\n")
    
    # Analyze each chat
    problematic_chats = []
    
    for i, composer in enumerate(all_composers):
        if not isinstance(composer, dict):
            continue
        
        comp_id = composer.get('id') or composer.get('composerId')
        title = composer.get('title') or composer.get('name') or composer.get('label') or 'Untitled'
        
        # Check for issues
        issues = []
        
        # Check if archived
        if composer.get('isArchived'):
            issues.append("ARCHIVED")
        
        # Check if hidden
        if composer.get('isHidden'):
            issues.append("HIDDEN")
        
        # Check if draft
        if composer.get('isDraft'):
            issues.append("DRAFT")
        
        # Check for missing required fields
        if not comp_id:
            issues.append("NO_ID")
        
        # Check for very old timestamps
        created = composer.get('createdAt', 0)
        updated = composer.get('lastUpdatedAt', composer.get('updatedAt', 0))
        
        # Check if has blocking actions
        if composer.get('hasBlockingPendingActions'):
            issues.append("BLOCKING_ACTIONS")
        
        # Check structure
        if 'type' not in composer:
            issues.append("NO_TYPE")
        
        # Check for problematic chats
        if 'recurring' in title.lower() or 'stuck' in title.lower():
            print(f"[RECURRING CHAT] {title}")
            print(f"  ID: {comp_id}")
            print(f"  Issues: {', '.join(issues) if issues else 'None'}")
            print(f"  Created: {created}")
            print(f"  Updated: {updated}")
            print(f"  Keys: {list(composer.keys())[:10]}")
            print()
            problematic_chats.append((comp_id, title, issues, composer))
        
        if 'youtube' in title.lower() or 'generated video' in title.lower():
            print(f"[PROBLEMATIC CHAT] {title}")
            print(f"  ID: {comp_id}")
            print(f"  Issues: {', '.join(issues) if issues else 'None'}")
            print(f"  Created: {created}")
            print(f"  Updated: {updated}")
            print(f"  Keys: {list(composer.keys())[:10]}")
            print()
            problematic_chats.append((comp_id, title, issues, composer))
    
    # Check prompts and generations
    print("\n" + "=" * 60)
    print("CHECKING PROMPTS AND GENERATIONS")
    print("=" * 60)
    
    cursor.execute("SELECT LENGTH(value) FROM ItemTable WHERE key = 'aiService.prompts'")
    row = cursor.fetchone()
    if row:
        print(f"Prompts size: {row[0]/1024:.1f} KB")
        
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'aiService.prompts'")
        row = cursor.fetchone()
        if row:
            prompts = json.loads(row[0])
            count = len(prompts) if isinstance(prompts, list) else 'N/A'
            print(f"Prompts count: {count}")
    
    cursor.execute("SELECT LENGTH(value) FROM ItemTable WHERE key = 'aiService.generations'")
    row = cursor.fetchone()
    if row:
        print(f"Generations size: {row[0]/1024:.1f} KB")
        
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'aiService.generations'")
        row = cursor.fetchone()
        if row:
            generations = json.loads(row[0])
            count = len(generations) if isinstance(generations, list) else 'N/A'
            print(f"Generations count: {count}")
    
    # Check selected chats
    print("\n" + "=" * 60)
    print("SELECTED CHATS")
    print("=" * 60)
    selected = composer_data.get('selectedComposerIds', [])
    focused = composer_data.get('lastFocusedComposerIds', [])
    print(f"Selected: {selected}")
    print(f"Focused: {focused}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Found {len(problematic_chats)} potentially problematic chats")
    print("\nCommon issues found:")
    for comp_id, title, issues, composer in problematic_chats:
        if issues:
            print(f"  {title}: {', '.join(issues)}")
    
    return problematic_chats

if __name__ == "__main__":
    investigate()


"""
Read Cursor's state database to find chat
"""
import os
import sqlite3
import json
from pathlib import Path

def read_state_db():
    """Read the state.vscdb database"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    db_file = storage / "state.vscdb"
    
    if not db_file.exists():
        print("Database not found")
        return
    
    print(f"Reading database: {db_file}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTables found: {[t[0] for t in tables]}")
        
        # Search for chat-related tables
        for table in tables:
            table_name = table[0]
            if 'chat' in table_name.lower() or 'conversation' in table_name.lower():
                print(f"\n[FOUND] Table: {table_name}")
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    print(f"  Rows: {len(rows)}")
                    if rows:
                        # Get column names
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        cols = [col[1] for col in cursor.fetchall()]
                        print(f"  Columns: {cols}")
                        
                        # Search for "Recurring" in all text columns
                        for col in cols:
                            try:
                                cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE '%Recurring%' OR {col} LIKE '%stuck%'")
                                matches = cursor.fetchall()
                                if matches:
                                    print(f"\n  [MATCH FOUND] in column {col}")
                                    for match in matches[:3]:
                                        print(f"    {match}")
                            except:
                                pass
                except Exception as e:
                    print(f"  Error reading table: {e}")
        
        # Also try to search all tables for text containing "Recurring"
        print("\n" + "=" * 60)
        print("Searching all tables for 'Recurring' or 'stuck'...")
        for table in tables:
            table_name = table[0]
            try:
                # Get all columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                cols = [col[1] for col in cursor.fetchall()]
                
                # Search each text column
                for col in cols:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE '%Recurring%' OR {col} LIKE '%stuck issue%'")
                        matches = cursor.fetchall()
                        if matches:
                            print(f"\n[FOUND MATCH] in {table_name}.{col}")
                            # Save the matches
                            output = Path("./recovered_chat_from_db.json")
                            with open(output, 'w', encoding='utf-8') as f:
                                json.dump({
                                    'table': table_name,
                                    'column': col,
                                    'matches': [str(m) for m in matches]
                                }, f, indent=2)
                            print(f"  [SAVED] {output}")
                    except:
                        pass
            except:
                pass
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    read_state_db()


























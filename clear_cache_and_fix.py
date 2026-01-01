"""
Clear Cursor cache and ensure chat works
"""
import os
import shutil
from pathlib import Path

def clear_cache():
    """Clear Cursor cache that might be preventing chat from opening"""
    storage = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "workspaceStorage" / "f7257ad7e6ee532686cf723015fac008"
    
    print("=" * 60)
    print("CLEARING CURSOR CACHE")
    print("=" * 60)
    
    cache_dirs = ['cache', 'CachedData', 'Cache', 'cached']
    
    cleared = False
    for cache_name in cache_dirs:
        cache_dir = storage / cache_name
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"[CLEARED] {cache_name}/")
                cleared = True
            except Exception as e:
                print(f"[WARNING] Could not clear {cache_name}: {e}")
    
    if not cleared:
        print("[INFO] No cache directories found to clear")
    
    print("\n" + "=" * 60)
    print("CACHE CLEARED")
    print("=" * 60)
    print("\nNow:")
    print("1. Close Cursor completely")
    print("2. Restart Cursor")
    print("3. The chat should work now (cache was cleared)")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    clear_cache()


















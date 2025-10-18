"""
Cleanup script to remove obsolete and duplicate files from TrueFACE Backend
"""

import os
import sys
from pathlib import Path

def cleanup_files():
    """Remove obsolete and duplicate files"""
    
    # Files to remove (obsolete/duplicate)
    obsolete_files = [
        'main_original.py',      # Backup of insecure original
        'main_secure.py',        # Duplicate of current main.py
        'main_simple.py',        # Simple version used during development
        'deepfake_model.py',     # Original placeholder model
        'test_api.py',           # Original test without security
        'test_simple.py',        # Simple test without authentication
        'test_real_models.py',   # Standalone model test
        'quick_test.py',         # Temporary debugging test
        'start.py',              # Original startup script
        '.env.example',          # Redundant environment file
        'trueface_backend.log',  # Log file (should be gitignored)
    ]
    
    print("🧹 TrueFACE Backend Cleanup")
    print("=" * 40)
    
    current_dir = Path.cwd()
    removed_count = 0
    
    for filename in obsolete_files:
        file_path = current_dir / filename
        
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Removed: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {filename}: {e}")
        else:
            print(f"ℹ️  Not found: {filename}")
    
    print(f"\n📊 Summary: {removed_count} obsolete files removed")
    
    # Show remaining files
    print(f"\n📁 Remaining files in {current_dir.name}:")
    remaining_files = [f for f in os.listdir(current_dir) if os.path.isfile(f)]
    remaining_files.sort()
    
    for file in remaining_files:
        if not file.startswith('.') and not file.endswith('.pyc'):
            print(f"   📄 {file}")
    
    print(f"\n✨ Cleanup complete! Directory is now organized.")

if __name__ == "__main__":
    cleanup_files()

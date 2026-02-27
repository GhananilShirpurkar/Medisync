#!/usr/bin/env python3
"""
PROJECT CLEANUP SCRIPT
======================
Automatically removes unnecessary files and keeps project clean.

Usage:
    python backend/scripts/cleanup_project.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without actually deleting
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------

# Files/patterns to always keep (never delete)
KEEP_FILES = {
    'README.md',
    'HACKFUSION-PLAN.md',
    'HACKFUSION-RESOURCES-MAPPING.md',
    'CONTINUE-DEVELOPMENT.md',
    'CONTINUE-DEVELOPMENT-V1-BACKUP.md',
    'CHECKUP.md',
    'SETUP-COMPLETE.md',
    '.gitignore',
    '.env',
    '.env.example',
    '.task_counter',
    'package.json',
    'package-lock.json',
    'requirements.txt',
    'main.py',
    'App.jsx',
    'vite.config.js',
    'index.html',
    'eslint.config.js',
}

# Patterns for files to delete
DELETE_PATTERNS = [
    '*_temp.py',
    '*_old.py',
    '*_backup.py',
    'temp_*.py',
    'debug_*.py',
    'scratch_*.py',
    '*-OLD.md',
    '*-BACKUP.md',
    '*-COPY.md',
    '*-TEMP.md',
    'TASK-*.md',  # Task completion summaries
    'CHANGES-APPLIED.md',
    'CLEANUP-SUMMARY.md',
    'FILES-TO-DELETE.md',
    'PROJECT-ANALYSIS-REPORT.md',
]

# Directories to clean (remove entirely)
CLEAN_DIRS = [
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    'htmlcov',
    '.coverage',
    '*.egg-info',
]

# Directories to skip entirely (never clean)
SKIP_DIRS = {
    '.venv',
    'venv',
    'node_modules',
    '.git',
    '.agent',
    'data',  # Keep data files
}

# File extensions to remove
CLEAN_EXTENSIONS = [
    '.pyc',
    '.pyo',
    '.pyd',
    '.so',
    '.dll',
    '.dylib',
]


# ------------------------------------------------------------------
# CLEANUP FUNCTIONS
# ------------------------------------------------------------------

def cleanup_cache_dirs(root_dir: Path, dry_run: bool = False) -> List[str]:
    """Remove Python cache directories."""
    removed = []
    
    for pattern in CLEAN_DIRS:
        for path in root_dir.rglob(pattern):
            # Skip if in excluded directory
            if any(skip_dir in path.parts for skip_dir in SKIP_DIRS):
                continue
                
            if path.is_dir():
                removed.append(str(path))
                if not dry_run:
                    shutil.rmtree(path)
                    print(f"  🗑️  Removed directory: {path}")
                else:
                    print(f"  [DRY RUN] Would remove: {path}")
    
    return removed


def cleanup_cache_files(root_dir: Path, dry_run: bool = False) -> List[str]:
    """Remove cache files by extension."""
    removed = []
    
    for ext in CLEAN_EXTENSIONS:
        for path in root_dir.rglob(f'*{ext}'):
            # Skip if in excluded directory
            if any(skip_dir in path.parts for skip_dir in SKIP_DIRS):
                continue
                
            if path.is_file():
                removed.append(str(path))
                if not dry_run:
                    path.unlink()
                    print(f"  🗑️  Removed file: {path}")
                else:
                    print(f"  [DRY RUN] Would remove: {path}")
    
    return removed


def cleanup_temp_files(root_dir: Path, dry_run: bool = False) -> List[str]:
    """Remove temporary files matching patterns."""
    removed = []
    
    for pattern in DELETE_PATTERNS:
        for path in root_dir.rglob(pattern):
            # Skip if in excluded directory
            if any(skip_dir in path.parts for skip_dir in SKIP_DIRS):
                continue
                
            if path.is_file() and path.name not in KEEP_FILES:
                removed.append(str(path))
                if not dry_run:
                    path.unlink()
                    print(f"  🗑️  Removed temp file: {path}")
                else:
                    print(f"  [DRY RUN] Would remove: {path}")
    
    return removed


def cleanup_empty_files(root_dir: Path, dry_run: bool = False) -> List[str]:
    """Remove empty or near-empty files (< 3 lines)."""
    removed = []
    
    for ext in ['.py', '.md', '.txt']:
        for path in root_dir.rglob(f'*{ext}'):
            # Skip if in excluded directory
            if any(skip_dir in path.parts for skip_dir in SKIP_DIRS):
                continue
                
            if path.is_file() and path.name not in KEEP_FILES:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Remove if empty or only whitespace
                    # BUT: Keep __init__.py files even if empty (they're needed for Python packages)
                    if path.name == '__init__.py':
                        continue
                        
                    if len(lines) < 3 and all(line.strip() == '' for line in lines):
                        removed.append(str(path))
                        if not dry_run:
                            path.unlink()
                            print(f"  🗑️  Removed empty file: {path}")
                        else:
                            print(f"  [DRY RUN] Would remove empty: {path}")
                except Exception as e:
                    print(f"  ⚠️  Could not check {path}: {e}")
    
    return removed


def get_dir_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"


# ------------------------------------------------------------------
# MAIN CLEANUP
# ------------------------------------------------------------------

def main():
    """Run project cleanup."""
    parser = argparse.ArgumentParser(description='Clean up project files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    args = parser.parse_args()
    
    # Get project root (2 levels up from this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    print("=" * 60)
    print("🧹 PROJECT CLEANUP")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()
    
    # Calculate initial size
    initial_size = get_dir_size(project_root)
    print(f"Initial project size: {format_size(initial_size)}")
    print()
    
    # Track all removed files
    all_removed = []
    
    # 1. Clean cache directories
    print("1️⃣  Cleaning cache directories...")
    removed = cleanup_cache_dirs(project_root, args.dry_run)
    all_removed.extend(removed)
    print(f"   Removed {len(removed)} cache directories")
    print()
    
    # 2. Clean cache files
    print("2️⃣  Cleaning cache files...")
    removed = cleanup_cache_files(project_root, args.dry_run)
    all_removed.extend(removed)
    print(f"   Removed {len(removed)} cache files")
    print()
    
    # 3. Clean temporary files
    print("3️⃣  Cleaning temporary files...")
    removed = cleanup_temp_files(project_root, args.dry_run)
    all_removed.extend(removed)
    print(f"   Removed {len(removed)} temporary files")
    print()
    
    # 4. Clean empty files
    print("4️⃣  Cleaning empty files...")
    removed = cleanup_empty_files(project_root, args.dry_run)
    all_removed.extend(removed)
    print(f"   Removed {len(removed)} empty files")
    print()
    
    # Calculate final size
    final_size = get_dir_size(project_root)
    saved = initial_size - final_size
    
    # Summary
    print("=" * 60)
    print("✅ CLEANUP COMPLETE")
    print("=" * 60)
    print(f"Total files/dirs removed: {len(all_removed)}")
    print(f"Initial size: {format_size(initial_size)}")
    print(f"Final size: {format_size(final_size)}")
    print(f"Space saved: {format_size(saved)}")
    print()
    
    if args.dry_run:
        print("⚠️  This was a DRY RUN - no files were actually deleted")
        print("   Run without --dry-run to perform actual cleanup")
    else:
        print("✅ Project cleaned successfully!")
        print()
        print("Next steps:")
        print("  1. Verify project still works: python backend/tests/test_ocr_service.py")
        print("  2. Check frontend builds: cd frontend && npm run build")
        print("  3. Continue development!")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

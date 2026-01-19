"""
Directory reorganization script for FYN-X.
Cleans up clutter and organizes files into logical directories.
"""

import shutil
from pathlib import Path
import sys


def create_directory_structure():
    """Create the new directory structure."""
    print("\n" + "="*60)
    print("CREATING NEW DIRECTORY STRUCTURE")
    print("="*60)
    
    directories = {
        'docs': 'Documentation files',
        'tests': 'Test files',
        'server': 'AI model and server files',
        'scripts': 'Utility scripts',
    }
    
    for dir_name, description in directories.items():
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"✓ Created: {dir_name}/ ({description})")
        else:
            print(f"  Exists: {dir_name}/")


def move_documentation():
    """Move .md files to docs/ directory."""
    print("\n" + "="*60)
    print("ORGANIZING DOCUMENTATION")
    print("="*60)
    
    # Files to keep in root
    keep_in_root = {
        'README.md',
        'QUICKSTART.md',
        'DEVELOPMENT.md',
    }
    
    # Find all .md files in root
    md_files = list(Path('.').glob('*.md'))
    
    moved_count = 0
    for md_file in md_files:
        if md_file.name in keep_in_root:
            print(f"  Keeping: {md_file.name} (in root)")
        else:
            dest = Path('docs') / md_file.name
            if not dest.exists():
                shutil.move(str(md_file), str(dest))
                print(f"✓ Moved: {md_file.name} → docs/")
                moved_count += 1
            else:
                print(f"  Skipped: {md_file.name} (already in docs/)")
    
    print(f"\nMoved {moved_count} documentation files to docs/")


def move_model_files():
    """Move model files to server/ directory."""
    print("\n" + "="*60)
    print("ORGANIZING SERVER FILES")
    print("="*60)
    
    server_files = {
        'FYN-X.modelfile': 'Main model definition',
        'FYN-X-fast.modelfile': 'Fast model definition',
        'rebuild_model.py': 'Model rebuild script',
    }
    
    moved_count = 0
    for filename, description in server_files.items():
        src = Path(filename)
        if src.exists():
            dest = Path('server') / filename
            if not dest.exists():
                shutil.move(str(src), str(dest))
                print(f"✓ Moved: {filename} → server/ ({description})")
                moved_count += 1
            else:
                print(f"  Skipped: {filename} (already in server/)")
        else:
            print(f"  Missing: {filename}")
    
    print(f"\nMoved {moved_count} server files")


def move_test_files():
    """Move test files to tests/ directory."""
    print("\n" + "="*60)
    print("ORGANIZING TEST FILES")
    print("="*60)
    
    test_patterns = [
        'test_*.py',
        '*_test.py',
    ]
    
    moved_count = 0
    for pattern in test_patterns:
        for test_file in Path('.').glob(pattern):
            dest = Path('tests') / test_file.name
            if not dest.exists():
                shutil.move(str(test_file), str(dest))
                print(f"✓ Moved: {test_file.name} → tests/")
                moved_count += 1
    
    print(f"\nMoved {moved_count} test files")


def create_docs_index():
    """Create an index file in docs/."""
    print("\n" + "="*60)
    print("CREATING DOCUMENTATION INDEX")
    print("="*60)
    
    index_content = """# FYN-X Documentation Index

## Quick Start
- [README](../README.md) - Project overview
- [QUICKSTART](../QUICKSTART.md) - Getting started guide
- [DEVELOPMENT](../DEVELOPMENT.md) - Development guide

## Setup & Configuration
- [GPU_OPTIMIZATION.md](GPU_OPTIMIZATION.md) - GPU setup and troubleshooting
- [TTS_INTEGRATION.md](TTS_INTEGRATION.md) - Text-to-speech setup
- [CAMERA_SETUP.md](CAMERA_SETUP.md) - Camera and face recognition setup
- [MICROPHONE_SETUP.md](MICROPHONE_SETUP.md) - Voice input setup

## Features & Improvements
- [AUTO_NAME_DETECTION.md](AUTO_NAME_DETECTION.md) - Automatic name detection
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Feature improvements log
- [BUG_FIXES.md](BUG_FIXES.md) - Bug fixes and solutions

## Reference
- [QUICKREFERENCE.md](QUICKREFERENCE.md) - Command reference
- [COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md) - Complete feature summary
- [SUMMARY.md](SUMMARY.md) - Project summary

## Architecture
- Project structure
- Module documentation
- API reference (coming soon)
"""
    
    index_file = Path('docs/INDEX.md')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"✓ Created: docs/INDEX.md")


def create_server_readme():
    """Create README in server/ directory."""
    print("\n" + "="*60)
    print("CREATING SERVER README")
    print("="*60)
    
    readme_content = """# FYN-X Server / AI Model

This directory contains AI model configuration and server-related files.

## Files

- **FYN-X.modelfile** - Main Ollama model definition
- **FYN-X-fast.modelfile** - Fast model variant
- **rebuild_model.py** - Script to rebuild model with latest fixes

## Rebuilding the Model

After making changes to the modelfile:

```bash
cd server
python rebuild_model.py
```

Or manually:

```bash
ollama rm FYN-X
ollama create FYN-X -f FYN-X.modelfile
```

## Model Parameters

Current configuration (in FYN-X.modelfile):
- `num_gpu 999` - Use all available GPU layers
- `num_thread 8` - CPU threads for parallel processing  
- `num_ctx 8192` - Context window size

See [GPU_OPTIMIZATION.md](../docs/GPU_OPTIMIZATION.md) for tuning guide.
"""
    
    readme_file = Path('server/README.md')
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ Created: server/README.md")


def print_new_structure():
    """Print the new directory structure."""
    print("\n" + "="*60)
    print("NEW DIRECTORY STRUCTURE")
    print("="*60)
    
    structure = """
fynx/
├── server/              # AI model and server configuration
│   ├── FYN-X.modelfile
│   ├── FYN-X-fast.modelfile
│   ├── rebuild_model.py
│   └── README.md
│
├── src/                 # Source code modules
│   ├── memory.py        # Memory management
│   ├── streaming.py     # Streaming output
│   ├── tts.py          # Text-to-speech
│   ├── stt.py          # Speech-to-text (NEW)
│   ├── camera.py       # Camera & face recognition (NEW)
│   ├── network.py       # Network communication
│   └── ...
│
├── edge-compute/        # Edge device specific code
│   └── ...
│
├── data/                # Data storage
│   ├── memories.json    # Conversation memories
│   ├── faces/          # Face recognition data (NEW)
│   └── performance_log.json
│
├── docs/                # Documentation
│   ├── INDEX.md        # Documentation index (NEW)
│   ├── GPU_OPTIMIZATION.md
│   ├── TTS_INTEGRATION.md
│   ├── CAMERA_SETUP.md (NEW)
│   ├── MICROPHONE_SETUP.md (NEW)
│   ├── BUG_FIXES.md
│   ├── AUTO_NAME_DETECTION.md
│   └── ...
│
├── tests/               # Test files
│   ├── test_improvements.py
│   ├── test_components.py
│   └── ...
│
├── scripts/             # Utility scripts (future)
│   └── ...
│
├── FYNX_run.py         # Main application
├── README.md           # Project overview
├── QUICKSTART.md       # Quick start guide
├── DEVELOPMENT.md      # Development guide
└── .gitignore
"""
    
    print(structure)


def main():
    """Main reorganization process."""
    print("\n" + "="*70)
    print(" " * 20 + "FYN-X DIRECTORY CLEANUP")
    print("="*70)
    
    print("\nThis script will:")
    print("  1. Create new directory structure (docs/, tests/, server/)")
    print("  2. Move .md files to docs/ (except README, QUICKSTART, DEVELOPMENT)")
    print("  3. Move model files to server/")
    print("  4. Move test files to tests/")
    print("  5. Create helpful index files")
    
    response = input("\nProceed with reorganization? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    try:
        # Step 1: Create directories
        create_directory_structure()
        
        # Step 2: Move documentation
        move_documentation()
        
        # Step 3: Move server files
        move_model_files()
        
        # Step 4: Move test files
        move_test_files()
        
        # Step 5: Create index files
        create_docs_index()
        create_server_readme()
        
        # Show new structure
        print_new_structure()
        
        print("\n" + "="*70)
        print("✓ REORGANIZATION COMPLETE!")
        print("="*70)
        
        print("\nNext steps:")
        print("  1. Check that everything moved correctly")
        print("  2. Update any import paths if needed")
        print("  3. See docs/INDEX.md for documentation overview")
        print("  4. Rebuild model from server/: python server/rebuild_model.py")
        
    except Exception as e:
        print(f"\n✗ Error during reorganization: {e}")
        print("Some files may have been moved. Check directories manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()

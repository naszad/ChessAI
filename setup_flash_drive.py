import os
import shutil
import sys
from pathlib import Path

def check_flash_drive():
    """Check if flash drive is available and has enough space."""
    if not os.path.exists("D:\\"):
        print("Error: Flash drive D: not found. Please insert the flash drive.")
        return False
        
    # Check available space (need at least 2GB for database and model)
    try:
        total, used, free = shutil.disk_usage("D:\\")
        free_gb = free / (2**30)  # Convert to GB
        if free_gb < 2:
            print(f"Warning: Only {free_gb:.1f}GB available on flash drive.")
            print("Recommend at least 2GB free space for database and model.")
            return False
        print(f"Flash drive D: found with {free_gb:.1f}GB free space.")
        return True
    except Exception as e:
        print(f"Error checking flash drive: {e}")
        return False

def setup_project():
    """Set up the project structure on the flash drive."""
    # Get current directory (where this script is)
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Project directories to create
    directories = [
        "data",
        "games",
        "models",
        "utils",
        "checkpoints"
    ]
    
    # Files to copy (relative to project root)
    files_to_copy = [
        "config.py",
        "requirements.txt",
        "train.py",
        "example.py",
        "inference.py",
        "data/download_games.py",
        "data/chess_dataset.py",
        "models/chess_model.py",
        "utils/board_utils.py"
    ]
    
    # Create project root on flash drive
    flash_drive_root = Path("D:/ChessAI")
    
    try:
        # Create directories
        print("\nCreating directory structure...")
        for directory in directories:
            dir_path = flash_drive_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created {dir_path}")
        
        # Copy files
        print("\nCopying project files...")
        for file_path in files_to_copy:
            src = current_dir / file_path
            dst = flash_drive_root / file_path
            
            # Create parent directories if they don't exist
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Copied {file_path}")
            else:
                print(f"Warning: Source file not found: {src}")
        
        # Copy existing database file if present
        games_dir = current_dir / "games"
        if games_dir.exists():
            for file in games_dir.glob("*.pgn.zst"):
                dst = flash_drive_root / "games" / file.name
                shutil.copy2(file, dst)
                print(f"\nCopied database file: {file.name}")
        
        print("\nSetup complete! Project copied to D:/ChessAI")
        print("\nYou can now run these commands in PowerShell:")
        print("1. Set-Location -Path 'D:\\ChessAI'  # or cd 'D:\\ChessAI'")
        print("2. python .\\data\\download_games.py  # Process games")
        print("3. python .\\train.py --pgn_files .\\games\\lichess_games_filtered.pgn  # Train model")
        
    except Exception as e:
        print(f"\nError during setup: {e}")
        return False
    
    return True

def verify_setup():
    """Verify the setup by checking critical files and imports."""
    print("\nVerifying setup...")
    
    # Check if we can import key dependencies
    try:
        import torch
        import chess
        import numpy
        print("✓ Required Python packages are installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    # Check critical files
    critical_files = [
        "D:/ChessAI/config.py",
        "D:/ChessAI/train.py",
        "D:/ChessAI/data/download_games.py",
        "D:/ChessAI/models/chess_model.py"
    ]
    
    all_files_present = True
    for file in critical_files:
        if os.path.exists(file):
            print(f"✓ Found {file}")
        else:
            print(f"✗ Missing {file}")
            all_files_present = False
    
    return all_files_present

def main():
    print("Chess AI Flash Drive Setup")
    print("=========================")
    
    if not check_flash_drive():
        return
    
    print("\nSetting up project on flash drive D:")
    if setup_project() and verify_setup():
        print("\nSetup successful! Your Chess AI project is ready to use on drive D:")
        print("\nTo change to the project directory in PowerShell, use either:")
        print("  Set-Location -Path 'D:\\ChessAI'")
        print("  # or the shorter version:")
        print("  cd 'D:\\ChessAI'")
    else:
        print("\nSetup encountered some issues. Please check the errors above.")

if __name__ == "__main__":
    main() 
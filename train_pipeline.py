import os
import sys
import argparse
from datetime import datetime, timedelta
import subprocess
from pathlib import Path
import shutil
import calendar
import humanize
from tqdm import tqdm

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import GAMES_DIR, CHECKPOINTS_DIR, FILTERED_GAMES_PATH

def get_downloaded_months():
    """Get a list of months that have already been downloaded and filtered."""
    months = []
    
    # Look for directories in GAMES_DIR that match YYYY-MM format
    for item in os.listdir(GAMES_DIR):
        dir_path = os.path.join(GAMES_DIR, item)
        if os.path.isdir(dir_path) and len(item) == 7 and item[4] == '-':
            # Check if filtered PGN file exists in this directory
            filtered_pgn = os.path.join(dir_path, 'lichess_games_filtered.pgn')
            if os.path.exists(filtered_pgn):
                months.append(item)
    
    # Sort chronologically from oldest to newest
    months.sort()
    return months

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n=== {description} ===")
    print(f"[INFO] Running command: {' '.join(cmd)}")
    try:
        # Set PYTHONUNBUFFERED=1 to ensure Python doesn't buffer the output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        # Run the command and stream output in real-time
        result = subprocess.run(
            cmd,
            env=env,
            check=False,  # Don't raise exception on non-zero return code
            stdout=None,  # Use default stdout (terminal)
            stderr=None,  # Use default stderr (terminal)
            text=True,
            bufsize=1
        )
        
        # Check for errors
        if result.returncode != 0:
            print(f"\n[ERROR] Error during {description}")
            print(f"[ERROR] Exit code: {result.returncode}")
            return False
        
        return True
    except Exception as e:
        print(f"\n[ERROR] Error during {description}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Train chess model pipeline")
    
    # Training arguments
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of epochs to train')
    parser.add_argument('--num_workers', type=int, default=2,
                        help='Number of data loading workers')
    parser.add_argument('--save_every', type=int, default=1,
                        help='Save checkpoint every N epochs')
    parser.add_argument('--max_positions', type=int, default=None,
                        help='Maximum number of positions to load (for debugging)')
    parser.add_argument('--resume_from', type=str,
                        help='Path to checkpoint to resume from')
    
    args = parser.parse_args()
    
    # Get list of downloaded months
    months = get_downloaded_months()
    if not months:
        print("[ERROR] No downloaded and filtered game files found")
        print("Please run download_games.py first")
        return
    
    print(f"Found {len(months)} months of downloaded games:")
    for month in months:
        print(f"  - {month}")
    
    # Construct list of PGN files
    pgn_files = [os.path.join(GAMES_DIR, month, 'lichess_games_filtered.pgn') 
                 for month in months]
    
    # Build training command
    cmd = [
        'python',
        'train.py',
        '--pgn_files'
    ] + pgn_files + [
        '--epochs', str(args.epochs),
        '--batch_size', str(args.batch_size),
        '--num_workers', str(args.num_workers),
        '--save_every', str(args.save_every)
    ]
    
    if args.max_positions:
        cmd.extend(['--max_positions', str(args.max_positions)])
    
    if args.resume_from:
        cmd.extend(['--resume_from', args.resume_from])
    
    # Run training
    success = run_command(cmd, "Training model")
    if not success:
        print("\n[ERROR] Training failed")
        return
    
    print("\n[SUCCESS] Training completed successfully")

if __name__ == '__main__':
    main()
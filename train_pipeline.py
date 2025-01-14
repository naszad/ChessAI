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

def get_previous_months(num_months):
    """Get a list of previous months in YYYY-MM format."""
    current_date = datetime.now()
    
    # Always start from two months ago to ensure data availability
    current_date = current_date.replace(day=1)  # First of current month
    current_date = current_date - timedelta(days=1)  # Last day of previous month
    current_date = current_date.replace(day=1)  # First of previous month
    current_date = current_date - timedelta(days=1)  # Last day of two months ago
    
    months = []
    for i in range(num_months):
        year = current_date.year
        month = current_date.month
        months.append(f"{year}-{month:02d}")  # Ensure two-digit month format
        
        # Move to previous month
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        current_date = current_date.replace(year=year, month=month, day=1)
    
    # Sort chronologically from oldest to newest
    months.reverse()
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
    parser = argparse.ArgumentParser(description="Automated chess model training pipeline")
    parser.add_argument('--months', type=int, default=6,
                        help='Number of previous months of data to download')
    parser.add_argument('--min_elo', type=int, default=2000,
                        help='Minimum Elo rating for games')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of epochs to train')
    parser.add_argument('--batch_size', type=int, default=256,
                        help='Batch size for training')
    parser.add_argument('--num_workers', type=int, default=4,
                        help='Number of data loading workers')
    parser.add_argument('--continue_training', action='store_true',
                        help='Continue training from the last checkpoint')
    args = parser.parse_args()

    print("\n=== Chess AI Training Pipeline ===")
    print("=================================")
    
    # Create necessary directories
    os.makedirs(GAMES_DIR, exist_ok=True)
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

    # Get list of months to download
    months = get_previous_months(args.months)
    print(f"\n[INFO] Will download and process data from months: {', '.join(months)}")

    # Process each month
    all_filtered_games = []
    start_time = datetime.now()
    
    for i, month in enumerate(months, 1):
        print(f"\n[INFO] Processing month {i}/{len(months)}: {month}")
        month_dir = os.path.join(GAMES_DIR, month)
        os.makedirs(month_dir, exist_ok=True)
        
        # Download and process the month's data
        download_cmd = [
            "python", "data/download_games.py",
            "--download",
            "--month", month,
            "--output-dir", month_dir,
            "--min-elo", str(args.min_elo),
            "--max-games", "100000"  # Limit to 10,000 games per month
        ]
        
        if not run_command(download_cmd, f"Downloading games for {month}"):
            print(f"[WARN] Skipping {month} due to download error")
            continue
        
        # If download was successful, the filtered games will be in the month directory
        month_filtered_path = os.path.join(month_dir, "lichess_games_filtered.pgn")
        if os.path.exists(month_filtered_path):
            all_filtered_games.append(month_filtered_path)
            file_size = os.path.getsize(month_filtered_path)
            print(f"[OK] Successfully processed games for {month} ({humanize.naturalsize(file_size, binary=True)})")
        else:
            print(f"[ERROR] No filtered games found for {month}")

    if not all_filtered_games:
        print("\n[ERROR] No data was successfully processed. Aborting training.")
        return

    elapsed = datetime.now() - start_time
    total_size = sum(os.path.getsize(f) for f in all_filtered_games)
    
    print(f"\n[INFO] Data Processing Summary:")
    print(f"  * Successfully processed {len(all_filtered_games)} months of data")
    print(f"  * Total data size: {humanize.naturalsize(total_size, binary=True)}")
    print(f"  * Processing time: {humanize.naturaldelta(elapsed)}")
    print("\n[INFO] Processed months:")
    for pgn in all_filtered_games:
        month = os.path.basename(os.path.dirname(pgn))
        size = os.path.getsize(pgn)
        print(f"  * {month}: {humanize.naturalsize(size, binary=True)}")

    # Find latest checkpoint if continuing training
    latest_epoch = 0
    if args.continue_training:
        checkpoints = list(Path(CHECKPOINTS_DIR).glob("model_epoch_*.pt"))
        if checkpoints:
            latest_checkpoint = max(checkpoints, key=lambda x: int(str(x).split("_")[-1].split(".")[0]))
            latest_epoch = int(str(latest_checkpoint).split("_")[-1].split(".")[0])
            print(f"\n[INFO] Continuing training from epoch {latest_epoch}")

    # Train the model
    train_cmd = [
        "python", "train.py",
        "--pgn_files"] + all_filtered_games + [
        "--epochs", str(args.epochs + latest_epoch),
        "--batch_size", str(args.batch_size),
        "--num_workers", str(args.num_workers),
        "--save_every", "1"
    ]

    if args.continue_training and latest_epoch > 0:
        train_cmd.extend([
            "--resume_from", os.path.join(CHECKPOINTS_DIR, f"model_epoch_{latest_epoch}.pt")
        ])

    if not run_command(train_cmd, "Training model"):
        print("\n[ERROR] Training failed!")
        return

    print("\n[OK] Training pipeline completed successfully!")
    print(f"[INFO] Model checkpoints are saved in: {CHECKPOINTS_DIR}")
    print("[INFO] You can now use the model with the GUI or inference script.")

if __name__ == "__main__":
    main()
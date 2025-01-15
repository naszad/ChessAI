import os
import subprocess

def get_hdd_path():
    """Get the path to the external HDD using its label."""
    label = "My Passport"
    base_path = f"/media/parmenides/{label}"
    
    # Check if the drive is mounted
    if not os.path.ismount(base_path):
        raise RuntimeError(f"External HDD '{label}' is not mounted. Please ensure it is connected and mounted.")
    
    return base_path

# Path to external hard drive
FLASH_DRIVE = get_hdd_path()

# Project directories
PROJECT_ROOT = os.path.join(FLASH_DRIVE, "ChessAI")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GAMES_DIR = os.path.join(PROJECT_ROOT, "games")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
CHECKPOINTS_DIR = os.path.join(PROJECT_ROOT, "checkpoints")
UTILS_DIR = os.path.join(PROJECT_ROOT, "utils")

# Create directories if they don't exist
for directory in [PROJECT_ROOT, DATA_DIR, GAMES_DIR, MODELS_DIR, CHECKPOINTS_DIR, UTILS_DIR]:
    os.makedirs(directory, exist_ok=True)

# File paths
FILTERED_GAMES_PATH = os.path.join(GAMES_DIR, "lichess_games_filtered.pgn")
RAW_GAMES_PATH = os.path.join(GAMES_DIR, "lichess_games_raw.pgn")
COMPRESSED_GAMES_PATH = os.path.join(GAMES_DIR, "lichess_games.pgn.zst")
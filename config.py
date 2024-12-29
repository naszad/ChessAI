import os

# Change this to your flash drive letter (e.g., "E:", "F:", etc.)
FLASH_DRIVE = "D:"

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
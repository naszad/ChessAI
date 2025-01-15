import chess
import chess.pgn
import numpy as np
import torch
from torch.utils.data import Dataset
import os
from tqdm import tqdm

from utils.board_utils import encode_board, move_to_index

class ChessDataset(Dataset):
    def __init__(self, pgn_files, max_positions=None):
        """
        Dataset for training the chess model.
        
        Args:
            pgn_files: List of PGN file paths
            max_positions: Maximum number of positions to load (for debugging)
        """
        self.samples = []
        self._load_games(pgn_files, max_positions)
    
    def _load_games(self, pgn_files, max_positions):
        """Load positions from PGN files."""
        num_positions = 0
        print(f"Starting to load games from {len(pgn_files)} files...")
        
        for pgn_path in pgn_files:
            if not os.path.exists(pgn_path):
                print(f"Warning: PGN file not found: {pgn_path}")
                continue
            
            print(f"\nProcessing file: {pgn_path}")
            position_count = 0
            
            # First count the number of games in the file
            game_count = 0
            with open(pgn_path) as pgn:
                while chess.pgn.read_game(pgn) is not None:
                    game_count += 1
            
            # Now process the games with a progress bar
            with open(pgn_path) as pgn:
                for _ in tqdm(range(game_count), desc="Processing games", unit="game"):
                    if max_positions and num_positions >= max_positions:
                        print(f"Reached maximum positions limit: {max_positions}")
                        return
                        
                    game = chess.pgn.read_game(pgn)
                    if game is None:
                        break
                    
                    # Extract result
                    result = game.headers.get("Result", "*")
                    if result == "1-0":
                        value = 1.0
                    elif result == "0-1":
                        value = -1.0
                    else:  # Draw or unknown
                        value = 0.0
                    
                    # Process all positions in the game
                    board = game.board()
                    for move in game.mainline_moves():
                        # Create training sample
                        encoded_board = encode_board(board)
                        move_index = move_to_index(move)
                        self.samples.append((encoded_board, move_index, value))
                        
                        # Make the move on the board
                        board.push(move)
                        num_positions += 1
                        position_count += 1
                        
                        if max_positions and num_positions >= max_positions:
                            print(f"Reached maximum positions limit: {max_positions}")
                            return
            
            print(f"Completed file: {position_count} positions extracted")
        
        print(f"\nFinished loading dataset: {len(self.samples)} total positions from {len(pgn_files)} files")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        # Unpack the tuple
        encoded_board, move_index, value = self.samples[idx]
        
        # Convert to tensors
        position = torch.tensor(encoded_board, dtype=torch.float32)
        
        # Create one-hot policy vector
        policy = torch.zeros(4096, dtype=torch.float32)
        policy[move_index] = 1.0
        
        # Create value tensor
        value = torch.tensor([value], dtype=torch.float32)
        
        return position, policy, value
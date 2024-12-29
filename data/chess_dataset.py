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
        
        for pgn_path in pgn_files:
            if not os.path.exists(pgn_path):
                print(f"Warning: PGN file not found: {pgn_path}")
                continue
                
            with open(pgn_path) as pgn:
                while True:
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
                        x = encode_board(board)
                        
                        # Create policy label (one-hot vector for the move)
                        policy = np.zeros(4096, dtype=np.float32)
                        move_idx = move_to_index(move)
                        policy[move_idx] = 1.0
                        
                        self.samples.append({
                            'position': x,
                            'policy': policy,
                            'value': value
                        })
                        
                        # Make the move on the board
                        board.push(move)
                        
                        num_positions += 1
                        if max_positions and num_positions >= max_positions:
                            return
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Convert to tensors
        position = torch.tensor(sample['position'], dtype=torch.float32)
        policy = torch.tensor(sample['policy'], dtype=torch.float32)
        value = torch.tensor([sample['value']], dtype=torch.float32)
        
        return position, policy, value
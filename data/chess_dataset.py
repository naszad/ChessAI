import chess
import chess.pgn
import numpy as np
import torch
from torch.utils.data import Dataset, IterableDataset
import os
from tqdm import tqdm
import mmap
import pickle
import tempfile

from utils.board_utils import encode_board, move_to_index

class ChessDataset(IterableDataset):
    def __init__(self, pgn_files, max_positions=None):
        """
        Memory-efficient dataset for training the chess model.
        
        Args:
            pgn_files: List of PGN file paths
            max_positions: Maximum number of positions to load (for debugging)
        """
        self.pgn_files = pgn_files
        self.max_positions = max_positions
        self.total_positions = 0
        
        # Create a temporary file to store position indices
        self.temp_dir = tempfile.mkdtemp()
        self.index_file = os.path.join(self.temp_dir, 'position_indices.pkl')
        
        # Calculate total positions and create index
        self._create_index()
    
    def _create_index(self):
        """Create an index of game positions for efficient access."""
        print(f"Starting to index games from {len(self.pgn_files)} files...")
        indices = []
        current_pos = 0
        
        for pgn_path in self.pgn_files:
            if not os.path.exists(pgn_path):
                print(f"Warning: PGN file not found: {pgn_path}")
                continue
            
            print(f"\nIndexing file: {pgn_path}")
            file_positions = 0
            
            # Count games first
            game_count = sum(1 for _ in open(pgn_path) if _.startswith('[Event '))
            
            with open(pgn_path) as pgn:
                for _ in tqdm(range(game_count), desc="Indexing games", unit="game"):
                    game = chess.pgn.read_game(pgn)
                    if game is None:
                        break
                    
                    # Extract result
                    result = game.headers.get("Result", "*")
                    value = 1.0 if result == "1-0" else (-1.0 if result == "0-1" else 0.0)
                    
                    # Store game start position in file
                    game_start = pgn.tell()
                    move_count = sum(1 for _ in game.mainline_moves())
                    
                    indices.append((pgn_path, game_start, move_count, value))
                    file_positions += move_count
                    current_pos += move_count
                    
                    if self.max_positions and current_pos >= self.max_positions:
                        break
            
            print(f"Indexed {file_positions} positions")
            self.total_positions = current_pos
            
            if self.max_positions and current_pos >= self.max_positions:
                break
        
        # Save indices to temporary file
        with open(self.index_file, 'wb') as f:
            pickle.dump(indices, f)
        
        print(f"\nFinished indexing: {self.total_positions} total positions")
    
    def __iter__(self):
        worker_info = torch.utils.data.get_worker_info()
        
        # Load indices
        with open(self.index_file, 'rb') as f:
            indices = pickle.load(f)
        
        # Partition indices if using multiple workers
        if worker_info is not None:
            per_worker = int(np.ceil(len(indices) / worker_info.num_workers))
            start = worker_info.id * per_worker
            end = min(start + per_worker, len(indices))
            indices = indices[start:end]
        
        # Process games
        for pgn_path, game_start, move_count, value in indices:
            with open(pgn_path) as pgn:
                pgn.seek(game_start)
                game = chess.pgn.read_game(pgn)
                
                if game is None:
                    continue
                
                board = game.board()
                for move in game.mainline_moves():
                    # Create training sample
                    encoded_board = encode_board(board)
                    move_index = move_to_index(move)
                    
                    # Make the move on the board
                    board.push(move)
                    
                    # Yield the sample
                    yield encoded_board, move_index, value
    
    def __len__(self):
        return self.total_positions
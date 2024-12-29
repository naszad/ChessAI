import chess
import numpy as np
import torch

def encode_board(board):
    """
    Encodes a chess board into a tensor representation suitable for neural network input.
    
    Args:
        board: python-chess Board object
        
    Returns:
        numpy array of shape (14, 8, 8) representing:
        - 12 channels for pieces (6 piece types x 2 colors)
        - 1 channel for side to move
        - 1 channel for castling rights
    """
    encoded = np.zeros((14, 8, 8), dtype=np.float32)
    
    # Mapping from piece types to channel indices
    piece_to_channel = {
        chess.PAWN: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 4,
        chess.KING: 5
    }
    
    # Fill piece planes
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            row = 7 - (square // 8)  # Flip row index since chess.SQUARES goes bottom to top
            col = square % 8
            base_channel = piece_to_channel[piece.piece_type]
            
            if piece.color == chess.WHITE:
                channel = base_channel
            else:
                channel = base_channel + 6  # Black pieces start at channel 6
                
            encoded[channel, row, col] = 1.0
    
    # Side to move channel (channel 12)
    if board.turn == chess.WHITE:
        encoded[12, :, :] = 1.0
    
    # Castling rights channel (channel 13)
    castling_rights = sum([
        board.has_kingside_castling_rights(chess.WHITE),
        board.has_queenside_castling_rights(chess.WHITE),
        board.has_kingside_castling_rights(chess.BLACK),
        board.has_queenside_castling_rights(chess.BLACK),
    ])
    encoded[13, :, :] = castling_rights / 4.0
    
    return encoded

def move_to_index(move):
    """
    Converts a chess move to a unique index.
    Simple encoding: from_square * 64 + to_square
    
    Args:
        move: python-chess Move object
        
    Returns:
        integer index representing the move
    """
    return move.from_square * 64 + move.to_square

def index_to_move(index):
    """
    Converts an index back to a chess move.
    
    Args:
        index: integer index representing the move
        
    Returns:
        python-chess Move object
    """
    from_square = index // 64
    to_square = index % 64
    return chess.Move(from_square, to_square)

def create_move_lookup():
    """
    Creates a lookup table for all possible moves.
    
    Returns:
        Dictionary mapping move indices to chess.Move objects
    """
    moves = {}
    for from_square in range(64):
        for to_square in range(64):
            move = chess.Move(from_square, to_square)
            index = move_to_index(move)
            moves[index] = move
    return moves
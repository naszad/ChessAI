import torch
import chess
import argparse
import os
from models.chess_model import ChessNet
from utils.board_utils import encode_board, index_to_move
import torch.nn.functional as F

class ChessEngine:
    def __init__(self, model_path, device=None):
        """
        Chess engine using the trained neural network.
        
        Args:
            model_path: Path to the saved model checkpoint
            device: torch.device to use (defaults to GPU if available)
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
            
        # Load model
        self.model = ChessNet()
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Loaded model from {model_path}")
        print(f"Using device: {self.device}")
    
    def evaluate_position(self, board):
        """
        Evaluate a chess position.
        
        Args:
            board: python-chess Board object
            
        Returns:
            tuple (value, best_move, move_probabilities):
                value: float in [-1, 1] indicating position evaluation
                best_move: python-chess Move object for the best move
                move_probabilities: list of (move, probability) tuples
        """
        with torch.no_grad():
            # Encode board
            x = encode_board(board)
            x = torch.tensor(x, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Get model predictions
            value, policy_logits = self.model(x)
            
            # Convert policy logits to probabilities
            policy_probs = F.softmax(policy_logits, dim=1).cpu().numpy()[0]
            
            # Get legal moves
            legal_moves = list(board.legal_moves)
            
            # Calculate probabilities for legal moves only
            move_probs = []
            for move in legal_moves:
                idx = move.from_square * 64 + move.to_square
                prob = policy_probs[idx]
                move_probs.append((move, prob))
            
            # Sort by probability
            move_probs.sort(key=lambda x: x[1], reverse=True)
            
            # Get best move
            best_move = move_probs[0][0] if move_probs else None
            
            return value.item(), best_move, move_probs
    
    def get_top_moves(self, board, num_moves=5):
        """
        Get the top N moves suggested by the model.
        
        Args:
            board: python-chess Board object
            num_moves: Number of top moves to return
            
        Returns:
            list of (move, probability, evaluation) tuples
        """
        value, _, move_probs = self.evaluate_position(board)
        return [(move, prob, value) for move, prob in move_probs[:num_moves]]
    
    def play_game(self):
        """
        Play an interactive game against the AI.
        Player plays as White, AI plays as Black.
        """
        board = chess.Board()
        
        while not board.is_game_over():
            # Print current board state
            print("\n" + str(board))
            
            if board.turn == chess.WHITE:
                # Player's turn
                while True:
                    try:
                        move_str = input("\nEnter your move (e.g. 'e2e4' or 'e4'): ")
                        # Try to parse as UCI first
                        try:
                            move = chess.Move.from_uci(move_str.lower())
                            if move in board.legal_moves:
                                break
                        except ValueError:
                            # Try to parse as SAN
                            try:
                                move = board.parse_san(move_str)
                                break
                            except ValueError:
                                print("Invalid move! Please try again.")
                    except KeyboardInterrupt:
                        print("\nGame aborted by user.")
                        return
                
                # Make player's move
                board.push(move)
                
            else:
                # AI's turn
                print("\nAI is thinking...")
                value, best_move, move_probs = self.evaluate_position(board)
                print(f"Evaluation: {value:.3f}")
                print("Top moves:")
                for i, (move, prob) in enumerate(move_probs[:3], 1):
                    print(f"{i}. {board.san(move):<6} ({prob:.3%})")
                
                # Make AI's move
                board.push(best_move)
                print(f"\nAI plays: {board.san(best_move)}")
        
        # Game over
        print("\nFinal position:")
        print(board)
        print("\nGame Over!")
        print(f"Result: {board.result()}")
        if board.is_checkmate():
            print("Checkmate!")
        elif board.is_stalemate():
            print("Stalemate!")
        elif board.is_insufficient_material():
            print("Draw by insufficient material!")
        elif board.is_fifty_moves():
            print("Draw by fifty-move rule!")
        elif board.is_repetition():
            print("Draw by repetition!")

def main():
    parser = argparse.ArgumentParser(description="Chess model inference")
    parser.add_argument('--model_path', type=str, required=True,
                        help='Path to the model checkpoint')
    parser.add_argument('--fen', type=str, default=chess.STARTING_FEN,
                        help='FEN string of the position to analyze')
    parser.add_argument('--num_moves', type=int, default=5,
                        help='Number of top moves to show')
    parser.add_argument('--cpu', action='store_true',
                        help='Force CPU inference')
    parser.add_argument('--interactive', action='store_true',
                        help='Play an interactive game against the AI')
    
    args = parser.parse_args()
    
    # Set device
    device = torch.device("cpu") if args.cpu else None
    
    # Create engine
    engine = ChessEngine(args.model_path, device)
    
    if args.interactive:
        # Play interactive game
        engine.play_game()
    else:
        # Analyze single position
        board = chess.Board(args.fen)
        value, best_move, move_probs = engine.evaluate_position(board)
        
        # Print results
        print(f"\nPosition evaluation: {value:.3f}")
        print(f"\nTop {args.num_moves} moves:")
        for i, (move, prob) in enumerate(move_probs[:args.num_moves], 1):
            print(f"{i}. {board.san(move):<6} ({prob:.3%})")

if __name__ == '__main__':
    main()
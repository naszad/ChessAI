import chess
from inference import ChessEngine
import os

def main():
    # Example position (Sicilian Defense after 1.e4 c5)
    fen = "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    
    # Check if we have a trained model
    model_path = os.path.join("checkpoints", "model_epoch_10.pt")
    if not os.path.exists(model_path):
        print(f"No trained model found at {model_path}")
        print("Please train the model first using train.py")
        return
    
    # Create engine
    engine = ChessEngine(model_path)
    
    # Create board from FEN
    board = chess.Board(fen)
    
    # Print current position
    print("\nCurrent position:")
    print(board)
    
    # Get evaluation and top moves
    value, best_move, move_probs = engine.evaluate_position(board)
    
    # Print evaluation
    print(f"\nPosition evaluation: {value:.3f}")
    print("(positive values favor White, negative values favor Black)")
    
    # Print top 5 moves
    print("\nTop 5 suggested moves:")
    for i, (move, prob) in enumerate(move_probs[:5], 1):
        print(f"{i}. {board.san(move):<6} ({prob:.1%})")
    
    # Make the best move and show the resulting position
    if best_move:
        print(f"\nMaking the best move: {board.san(best_move)}")
        board.push(best_move)
        print("\nResulting position:")
        print(board)
        
        # Get evaluation of the new position
        value, _, _ = engine.evaluate_position(board)
        print(f"\nNew position evaluation: {value:.3f}")

if __name__ == '__main__':
    main()
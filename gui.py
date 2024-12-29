import sys
import chess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
import os
from inference import ChessEngine

class ChessSquare(QLabel):
    clicked = pyqtSignal(int, int)  # row, col

    def __init__(self, row, col, size):
        super().__init__()
        self.row = row
        self.col = col
        self.size = size
        self.setFixedSize(size, size)
        self.setStyleSheet(self._get_background_color())
        
    def _get_background_color(self):
        is_light = (self.row + self.col) % 2 == 0
        color = "#FFFFFF" if is_light else "#769656"
        return f"background-color: {color};"
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.row, self.col)

class ChessBoard(QWidget):
    move_made = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.square_size = 80
        self.selected_square = None
        self.legal_moves = set()
        
        # Load piece images
        self.pieces = {}
        piece_path = "pieces"
        
        # Check if pieces directory exists
        if not os.path.exists(piece_path):
            print(f"Error: {piece_path} directory not found!")
            print("Please run download_pieces.py first to download the chess pieces.")
            sys.exit(1)
        
        # Map chess piece symbols to filenames
        piece_filenames = {
            'K': 'KING_WHITE.png',
            'Q': 'QUEEN_WHITE.png',
            'R': 'ROOK_WHITE.png',
            'B': 'BISHOP_WHITE.png',
            'N': 'KNIGHT_WHITE.png',
            'P': 'PAWN_WHITE.png',
            'k': 'KING_BLACK.png',
            'q': 'QUEEN_BLACK.png',
            'r': 'ROOK_BLACK.png',
            'b': 'BISHOP_BLACK.png',
            'n': 'KNIGHT_BLACK.png',
            'p': 'PAWN_BLACK.png',
        }
            
        for piece, filename in piece_filenames.items():
            image_path = os.path.join(piece_path, filename)
            if not os.path.exists(image_path):
                print(f"Error: {image_path} not found!")
                print("Please run download_pieces.py to download all chess pieces.")
                sys.exit(1)
                
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print(f"Error: Failed to load image {image_path}")
                sys.exit(1)
                
            self.pieces[piece] = pixmap.scaled(
                self.square_size, self.square_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            print(f"Loaded piece image: {filename}")
        
        # Create layout
        layout = QVBoxLayout()
        board_layout = QHBoxLayout()
        
        # Create squares
        self.squares = [[ChessSquare(row, col, self.square_size) 
                        for col in range(8)] for row in range(8)]
        
        # Add squares to layout
        board_widget = QWidget()
        board_layout = QVBoxLayout()
        board_layout.setSpacing(0)
        board_layout.setContentsMargins(0, 0, 0, 0)
        
        for row in range(8):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(0)
            for col in range(8):
                square = self.squares[row][col]
                square.clicked.connect(self.square_clicked)
                row_layout.addWidget(square)
            board_layout.addLayout(row_layout)
        
        board_widget.setLayout(board_layout)
        layout.addWidget(board_widget)
        self.setLayout(layout)
        
        self.update_board()
    
    def update_board(self):
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                square_idx = chess.square(col, 7-row)
                piece = self.board.piece_at(square_idx)
                
                # Clear any existing pixmap
                square.clear()
                
                # Set piece image if there is a piece
                if piece:
                    square.setPixmap(self.pieces[piece.symbol()])
                
                # Highlight selected square and legal moves
                if self.selected_square == (row, col):
                    square.setStyleSheet(f"{square._get_background_color()} border: 2px solid #FFFF00;")
                elif chess.square(col, 7-row) in [move.to_square for move in self.legal_moves]:
                    square.setStyleSheet(f"{square._get_background_color()} border: 2px solid #00FF00;")
                else:
                    square.setStyleSheet(square._get_background_color())
    
    def square_clicked(self, row, col):
        if self.selected_square is None:
            # First click - select piece
            square_idx = chess.square(col, 7-row)
            piece = self.board.piece_at(square_idx)
            if piece and piece.color == self.board.turn:
                self.selected_square = (row, col)
                self.legal_moves = [move for move in self.board.legal_moves 
                                  if move.from_square == square_idx]
        else:
            # Second click - make move if legal
            from_square = chess.square(self.selected_square[1], 7-self.selected_square[0])
            to_square = chess.square(col, 7-row)
            
            # Find the actual legal move object that matches our move
            legal_move = None
            for m in self.legal_moves:
                if m.from_square == from_square and m.to_square == to_square:
                    legal_move = m
                    break
            
            if legal_move is not None:
                # Store the move text before making the move
                move_text = self.board.san(legal_move)
                # Make the move
                self.board.push(legal_move)
                # Emit both the move and its text representation
                self.move_made.emit((legal_move, move_text))
            
            self.selected_square = None
            self.legal_moves = set()
        
        self.update_board()

class ChessGUI(QMainWindow):
    def __init__(self, engine_path):
        super().__init__()
        self.engine = ChessEngine(engine_path)
        self.move_stack = []  # Stack to store moves for undo/redo
        self.redo_stack = []  # Stack to store undone moves for redo
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Chess AI GUI')
        
        # Create central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()
        
        # Create chess board
        self.board_widget = ChessBoard()
        self.board_widget.move_made.connect(self.on_player_move)
        layout.addWidget(self.board_widget)
        
        # Create side panel
        side_panel = QWidget()
        side_layout = QVBoxLayout()
        
        # Evaluation display
        self.eval_label = QLabel('Evaluation: 0.0')
        side_layout.addWidget(self.eval_label)
        
        # Move history
        self.move_history = QTextEdit()
        self.move_history.setReadOnly(True)
        side_layout.addWidget(QLabel('Move History:'))
        side_layout.addWidget(self.move_history)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # New Game button
        new_game_btn = QPushButton('New Game')
        new_game_btn.clicked.connect(self.new_game)
        button_layout.addWidget(new_game_btn)
        
        # Undo button
        self.undo_btn = QPushButton('Undo')
        self.undo_btn.clicked.connect(self.undo_move)
        self.undo_btn.setEnabled(False)
        button_layout.addWidget(self.undo_btn)
        
        # Redo button
        self.redo_btn = QPushButton('Redo')
        self.redo_btn.clicked.connect(self.redo_move)
        self.redo_btn.setEnabled(False)
        button_layout.addWidget(self.redo_btn)
        
        side_layout.addLayout(button_layout)
        
        side_panel.setLayout(side_layout)
        layout.addWidget(side_panel)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.resize(1200, 800)
    
    def new_game(self):
        self.board_widget.board = chess.Board()
        self.board_widget.update_board()
        self.move_history.clear()
        self.eval_label.setText('Evaluation: 0.0')
        self.move_stack.clear()
        self.redo_stack.clear()
        self.update_button_states()
    
    def update_button_states(self):
        self.undo_btn.setEnabled(len(self.move_stack) > 0)
        self.redo_btn.setEnabled(len(self.redo_stack) > 0)
    
    def undo_move(self):
        if len(self.move_stack) >= 2:  # Undo both player and AI moves
            # Undo AI move
            ai_move = self.move_stack.pop()
            self.redo_stack.append(ai_move)
            self.board_widget.board.pop()
            
            # Undo player move
            player_move = self.move_stack.pop()
            self.redo_stack.append(player_move)
            self.board_widget.board.pop()
            
            # Update move history by removing the last complete move (both white and black)
            text = self.move_history.toPlainText()
            lines = text.split('\n')
            # Remove empty lines and keep only complete moves
            lines = [line for line in lines if line.strip()]
            # Remove last two lines (White and Black moves)
            if len(lines) >= 2:
                lines = lines[:-2]
            # Reconstruct text with proper formatting
            self.move_history.setText('\n'.join(lines + ['']))  # Add empty line at end
            
            self.board_widget.update_board()
            self.update_button_states()
            
            # Update evaluation
            value, _, _ = self.engine.evaluate_position(self.board_widget.board)
            self.eval_label.setText(f'Evaluation: {value:.3f}')
    
    def redo_move(self):
        if len(self.redo_stack) >= 2:  # Redo both player and AI moves
            # Redo player move
            player_move = self.redo_stack.pop()
            self.move_stack.append(player_move)
            move_text = self.board_widget.board.san(player_move)
            self.board_widget.board.push(player_move)
            self.move_history.append(f"White: {move_text}")
            
            # Redo AI move
            ai_move = self.redo_stack.pop()
            self.move_stack.append(ai_move)
            move_text = self.board_widget.board.san(ai_move)
            self.board_widget.board.push(ai_move)
            self.move_history.append(f"Black: {move_text}\n")
            
            self.board_widget.update_board()
            self.update_button_states()
            
            # Update evaluation
            value, _, _ = self.engine.evaluate_position(self.board_widget.board)
            self.eval_label.setText(f'Evaluation: {value:.3f}')
    
    def on_player_move(self, move_data):
        move, move_text = move_data
        # Clear redo stack when a new move is made
        self.redo_stack.clear()
        # Add move to stack
        self.move_stack.append(move)
        # Update move history with pre-computed move text
        self.move_history.append(f"White: {move_text}")
        
        if not self.board_widget.board.is_game_over():
            # AI's turn
            value, best_move, move_probs = self.engine.evaluate_position(self.board_widget.board)
            self.eval_label.setText(f'Evaluation: {value:.3f}')
            
            if best_move:
                # Store move text before making the move
                ai_move_text = self.board_widget.board.san(best_move)
                # Make the move
                self.board_widget.board.push(best_move)
                # Add AI move to stack
                self.move_stack.append(best_move)
                # Update history with stored text
                self.move_history.append(f"Black: {ai_move_text}\n")
                self.board_widget.update_board()
        
        if self.board_widget.board.is_game_over():
            result = self.board_widget.board.result()
            self.move_history.append(f"\nGame Over! Result: {result}")
        
        self.update_button_states()

def main():
    app = QApplication(sys.argv)
    
    # Create pieces directory and download images if needed
    if not os.path.exists('pieces'):
        os.makedirs('pieces')
        # Here you would need to add code to download or copy piece images
        print("Please add chess piece images to the 'pieces' directory")
        return
    
    engine_path = "D:/ChessAI/checkpoints/model_epoch_20.pt"  # Update this path
    gui = ChessGUI(engine_path)
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 
import sys
import chess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, QColorDialog, QFileDialog, QInputDialog, QTabWidget, QGroupBox, QSpinBox)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QActionGroup
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QTimer
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
    move_made = pyqtSignal(chess.Board, object)  # Send board state before move and move data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store reference to parent GUI
        self.board = chess.Board()
        self.square_size = 80
        self.selected_square = None
        self.legal_moves = set()
        self.flipped = False  # Track if board is flipped
        self.last_move = None  # Store the last move made
        
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
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create squares
        self.squares = [[ChessSquare(row, col, self.square_size) 
                        for col in range(8)] for row in range(8)]
        
        # Create board layout with coordinates if enabled
        board_container = QWidget()
        board_layout = QVBoxLayout()
        board_layout.setSpacing(0)
        board_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add file letters (a-h) on top if coordinates are enabled
        if self.parent and self.parent.settings['game']['show_coordinates']:
            file_layout = QHBoxLayout()
            file_layout.setSpacing(0)
            file_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add spacer for rank labels
            spacer = QLabel()
            spacer.setFixedSize(20, 20)
            file_layout.addWidget(spacer)
            
            # Add file letters (a to h from left to right when not flipped)
            for file in range(8):
                file_label = QLabel(chr(ord('a') + (file if not self.flipped else 7 - file)))
                file_label.setFixedSize(self.square_size, 20)
                file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                file_layout.addWidget(file_label)
            
            board_layout.addLayout(file_layout)
        
        # Create main board grid with rank numbers
        board_grid = QHBoxLayout()
        board_grid.setSpacing(0)
        board_grid.setContentsMargins(0, 0, 0, 0)
        
        # Add rank numbers on left if coordinates are enabled
        if self.parent and self.parent.settings['game']['show_coordinates']:
            rank_column = QVBoxLayout()
            rank_column.setSpacing(0)
            rank_column.setContentsMargins(0, 0, 0, 0)
            
            # Add rank numbers (8 to 1 from top to bottom when not flipped)
            for rank in range(8):
                rank_label = QLabel(str(8 - rank if not self.flipped else rank + 1))
                rank_label.setFixedSize(20, self.square_size)
                rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                rank_column.addWidget(rank_label)
            
            board_grid.addLayout(rank_column)
        
        # Create squares grid
        squares_widget = QWidget()
        squares_layout = QVBoxLayout()
        squares_layout.setSpacing(0)
        squares_layout.setContentsMargins(0, 0, 0, 0)
        
        for row in range(8):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(0)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            for col in range(8):
                square = self.squares[row][col]
                square.clicked.connect(self.square_clicked)
                row_layout.addWidget(square)
            
            squares_layout.addLayout(row_layout)
        
        squares_widget.setLayout(squares_layout)
        board_grid.addWidget(squares_widget)
        board_layout.addLayout(board_grid)
        
        board_container.setLayout(board_layout)
        layout.addWidget(board_container)
        self.setLayout(layout)
        
        self.update_board()
    
    def _get_square_color(self, row, col):
        """Get the background color for a square based on current theme."""
        if not self.parent:
            return "#FFFFFF" if (row + col) % 2 == 0 else "#769656"
        
        theme = self.parent.settings['visual']['board_theme']
        colors = self.parent.settings['visual']['colors'][theme if theme != 'Custom Colors' else 'custom']
        return colors['light'] if (row + col) % 2 == 0 else colors['dark']
    
    def update_board(self):
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                square_idx = self.get_square_position(row, col)
                piece = self.board.piece_at(square_idx)
                
                # Clear any existing pixmap
                square.clear()
                
                # Set piece image if there is a piece
                if piece:
                    square.setPixmap(self.pieces[piece.symbol()])
                
                # Get base color
                base_color = self._get_square_color(row, col)
                style = f"background-color: {base_color};"
                
                # Add highlights based on settings
                if self.parent:
                    # Selected piece highlight
                    if self.selected_square == (row, col):
                        style += f" border: 2px solid {self.parent.settings['visual']['highlight_colors']['selected_piece']};"
                    # Legal moves highlight
                    elif self.parent.settings['game']['show_legal_moves'] and square_idx in [move.to_square for move in self.legal_moves]:
                        style += f" border: 2px solid {self.parent.settings['visual']['highlight_colors']['legal_moves']};"
                    # Last move highlight
                    elif self.last_move and square_idx in [self.last_move.from_square, self.last_move.to_square]:
                        style += f" border: 2px solid {self.parent.settings['visual']['highlight_colors']['last_move']};"
                    # Check highlight
                    elif self.board.is_check() and piece and piece.piece_type == chess.KING and piece.color == self.board.turn:
                        style += f" border: 2px solid {self.parent.settings['visual']['highlight_colors']['check']};"
                
                square.setStyleSheet(style)
    
    def flip_board(self, flipped):
        """Flip the board view."""
        self.flipped = flipped
        if self.parent and self.parent.settings['game']['show_coordinates']:
            # Store current board state
            current_board = self.board.copy()
            
            # Reinitialize the board with new orientation
            self.__init__(self.parent)
            self.board = current_board
            
        self.update_board()
    
    def get_square_position(self, row, col):
        """Get the actual board position based on whether the board is flipped."""
        if self.flipped:
            return chess.square(7-col, row)  # Flip both row and column
        else:
            return chess.square(col, 7-row)  # Normal orientation
    
    def square_clicked(self, row, col):
        # Get the actual board position
        square_idx = self.get_square_position(row, col)
        
        if self.selected_square is None:
            # First click - select piece
            piece = self.board.piece_at(square_idx)
            if piece and piece.color == self.board.turn:
                self.selected_square = (row, col)
                self.legal_moves = [move for move in self.board.legal_moves 
                                  if move.from_square == square_idx]
                self.update_board()  # Update to show legal moves
        else:
            # Second click - make move if legal
            from_square = self.get_square_position(self.selected_square[0], self.selected_square[1])
            to_square = square_idx  # Use the actual board position
            
            # Find the actual legal move object that matches our move
            legal_move = None
            for m in self.legal_moves:
                if m.from_square == from_square and m.to_square == to_square:
                    legal_move = m
                    break
            
            if legal_move is not None:
                # Store the move text before making the move
                move_text = self.board.san(legal_move)
                # Send board state before move and move data
                self.move_made.emit(self.board.copy(), (legal_move, move_text))
            
            self.selected_square = None
            self.legal_moves = set()
            self.update_board()

class ChessGUI(QMainWindow):
    def __init__(self, engine_path):
        super().__init__()
        # Create two engines for White and Black
        self.white_engine = ChessEngine(engine_path)
        self.black_engine = ChessEngine(engine_path)  # Initially same as white
        self.move_stack = []
        self.redo_stack = []
        self.hint_move = None
        self.playing_as_white = True
        
        # Settings with default values
        self.settings = {
            'game': {
                'show_legal_moves': True,
                'show_coordinates': False,
            },
            'visual': {
                'board_theme': 'Classic Green',
                'colors': {
                    'Classic Green': {'light': "#FFFFFF", 'dark': "#769656"},
                    'Blue': {'light': "#FFFFFF", 'dark': "#4B7399"},
                    'Brown': {'light': "#EEEED2", 'dark': "#B58863"},
                    'custom': {'light': "#FFFFFF", 'dark': "#769656"}
                },
                'highlight_colors': {
                    'legal_moves': "#00FF00",
                    'selected_piece': "#FFFF00",
                    'last_move': "#0000FF",
                    'check': "#FF0000"
                }
            },
            'engine': {
                'white_model_path': engine_path,
                'black_model_path': engine_path,
                'eval_threshold': 0.1,
                'show_top_n': 3,
                'show_probabilities': True,
                'show_evaluation': True
            }
        }
        
        self.init_ui()
        self.create_menus()
    
    def create_menus(self):
        # Create menu bar
        menubar = self.menuBar()
        
        # Settings Menu
        settings_menu = menubar.addMenu('Settings')
        
        # Game Settings Submenu
        game_menu = settings_menu.addMenu('Game')
        
        # Show Legal Moves
        show_legal_moves = game_menu.addAction('Show Legal Moves')
        show_legal_moves.setCheckable(True)
        show_legal_moves.setChecked(self.settings['game']['show_legal_moves'])
        show_legal_moves.triggered.connect(lambda x: self.toggle_setting('game', 'show_legal_moves'))
        
        # Show Coordinates
        show_coordinates = game_menu.addAction('Show Coordinates')
        show_coordinates.setCheckable(True)
        show_coordinates.setChecked(self.settings['game']['show_coordinates'])
        show_coordinates.triggered.connect(lambda x: self.toggle_setting('game', 'show_coordinates'))
        
        # Visual Settings Submenu
        visual_menu = settings_menu.addMenu('Visual')
        
        # Board Theme Submenu
        theme_menu = visual_menu.addMenu('Board Theme')
        theme_group = QActionGroup(self)
        
        for theme in ['Classic Green', 'Blue', 'Brown', 'Custom Colors']:
            theme_action = theme_menu.addAction(theme)
            theme_action.setCheckable(True)
            theme_action.setChecked(self.settings['visual']['board_theme'] == theme)
            theme_group.addAction(theme_action)
            theme_action.triggered.connect(lambda x, t=theme: self.change_theme(t))
        
        # Move Highlight Colors Submenu
        highlight_menu = visual_menu.addMenu('Move Highlight Colors')
        
        for highlight_type, color in self.settings['visual']['highlight_colors'].items():
            action = highlight_menu.addAction(f'Set {highlight_type.replace("_", " ").title()} Color')
            action.triggered.connect(lambda x, h=highlight_type: self.choose_highlight_color(h))
        
        # AI/Engine Settings Submenu
        engine_menu = settings_menu.addMenu('AI/Engine')
        
        # White Model Selection
        select_white_model = engine_menu.addAction('Select White Model')
        select_white_model.triggered.connect(lambda: self.select_model_file('white'))
        
        # Black Model Selection
        select_black_model = engine_menu.addAction('Select Black Model')
        select_black_model.triggered.connect(lambda: self.select_model_file('black'))
        
        # Engine Settings Submenu
        engine_settings = engine_menu.addMenu('Engine Settings')
        
        # Evaluation Threshold
        eval_threshold = engine_settings.addAction('Set Evaluation Threshold')
        eval_threshold.triggered.connect(self.set_eval_threshold)
        
        # Show Top N Moves
        top_n = engine_settings.addAction('Set Top N Moves')
        top_n.triggered.connect(self.set_top_n_moves)
        
        # Show Move Probabilities
        show_probs = engine_settings.addAction('Show Move Probabilities')
        show_probs.setCheckable(True)
        show_probs.setChecked(self.settings['engine']['show_probabilities'])
        show_probs.triggered.connect(lambda x: self.toggle_setting('engine', 'show_probabilities'))
        
        # Show Position Evaluation
        show_eval = engine_settings.addAction('Show Position Evaluation')
        show_eval.setCheckable(True)
        show_eval.setChecked(self.settings['engine']['show_evaluation'])
        show_eval.triggered.connect(lambda x: self.toggle_setting('engine', 'show_evaluation'))
    
    def toggle_setting(self, category, setting):
        """Toggle a boolean setting."""
        self.settings[category][setting] = not self.settings[category][setting]
        self.apply_settings()
    
    def change_theme(self, theme):
        """Change the board theme."""
        self.settings['visual']['board_theme'] = theme
        if theme == 'Custom Colors':
            self.choose_custom_colors()
        self.apply_settings()
    
    def choose_custom_colors(self):
        """Open color picker for custom board colors."""
        light = QColorDialog.getColor(QColor(self.settings['visual']['colors']['custom']['light']))
        if light.isValid():
            dark = QColorDialog.getColor(QColor(self.settings['visual']['colors']['custom']['dark']))
            if dark.isValid():
                self.settings['visual']['colors']['custom']['light'] = light.name()
                self.settings['visual']['colors']['custom']['dark'] = dark.name()
                self.apply_settings()
    
    def choose_highlight_color(self, highlight_type):
        """Open color picker for highlight colors."""
        color = QColorDialog.getColor(QColor(self.settings['visual']['highlight_colors'][highlight_type]))
        if color.isValid():
            self.settings['visual']['highlight_colors'][highlight_type] = color.name()
            self.apply_settings()
    
    def select_model_file(self, side):
        """Open file dialog to select a model file for White or Black."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select Model File for {side.title()}", 
            "", 
            "Model Files (*.pt)"
        )
        if file_name:
            if side == 'white':
                self.settings['engine']['white_model_path'] = file_name
                self.white_engine = ChessEngine(file_name)
                self.white_model_label.setText(f"Model: {os.path.basename(file_name)}")
            else:
                self.settings['engine']['black_model_path'] = file_name
                self.black_engine = ChessEngine(file_name)
                self.black_model_label.setText(f"Model: {os.path.basename(file_name)}")
    
    def set_eval_threshold(self):
        """Open dialog to set evaluation threshold."""
        value, ok = QInputDialog.getDouble(self, "Set Evaluation Threshold", 
                                         "Enter threshold value (0.0 - 1.0):",
                                         self.settings['engine']['eval_threshold'],
                                         0.0, 1.0, 2)
        if ok:
            self.settings['engine']['eval_threshold'] = value
    
    def set_top_n_moves(self):
        """Open dialog to set number of top moves to show."""
        value, ok = QInputDialog.getInt(self, "Set Top N Moves", 
                                      "Enter number of moves to show:",
                                      self.settings['engine']['show_top_n'],
                                      1, 10)
        if ok:
            self.settings['engine']['show_top_n'] = value
    
    def apply_settings(self):
        """Apply the current settings to the GUI."""
        # Update board colors
        theme = self.settings['visual']['board_theme']
        colors = self.settings['visual']['colors'][theme if theme != 'Custom Colors' else 'custom']
        
        # Rebuild board if coordinates setting changed
        self.rebuild_board()
        
        # Update board display
        self.board_widget.update_board()
        
        # Update evaluation display
        self.eval_label.setVisible(self.settings['engine']['show_evaluation'])
    
    def rebuild_board(self):
        """Rebuild the board layout to show/hide coordinates."""
        # Store current board state and orientation
        current_board = self.board_widget.board.copy()
        current_flipped = self.board_widget.flipped
        
        # Create new board with current settings
        self.board_widget = ChessBoard(self)
        self.board_widget.board = current_board
        self.board_widget.flipped = current_flipped
        self.board_widget.move_made.connect(self.on_player_move)
        
        # Replace old board widget in layout
        old_board = self.centralWidget().layout().itemAt(0).widget()
        self.centralWidget().layout().replaceWidget(old_board, self.board_widget)
        old_board.deleteLater()
    
    def init_ui(self):
        self.setWindowTitle('Chess AI GUI')
        
        # Create central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()
        
        # Create chess board
        self.board_widget = ChessBoard(self)  # Pass self as parent
        self.board_widget.move_made.connect(self.on_player_move)
        layout.addWidget(self.board_widget)
        
        # Create side panel with tabs
        side_panel = QWidget()
        side_layout = QVBoxLayout()
        
        # Player color display
        self.color_label = QLabel('Playing as: White')
        side_layout.addWidget(self.color_label)
        
        # Evaluation display
        self.eval_label = QLabel('Evaluation: 0.0')
        side_layout.addWidget(self.eval_label)
        
        # Hint display
        self.hint_label = QLabel('')
        side_layout.addWidget(self.hint_label)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Move History Tab
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        # Move history
        self.move_history = QTextEdit()
        self.move_history.setReadOnly(True)
        history_layout.addWidget(QLabel('Move History:'))
        history_layout.addWidget(self.move_history)
        
        history_tab.setLayout(history_layout)
        tab_widget.addTab(history_tab, "Move History")
        
        # Self-Play Tab
        self_play_tab = QWidget()
        self_play_layout = QVBoxLayout()
        
        # White Model Group
        white_group = QGroupBox("White Player")
        white_layout = QVBoxLayout()
        
        # White model display and select button
        self.white_model_label = QLabel(f"Model: {os.path.basename(self.settings['engine']['white_model_path'])}")
        white_layout.addWidget(self.white_model_label)
        
        select_white_btn = QPushButton('Select Model')
        select_white_btn.clicked.connect(lambda: self.select_model_file('white'))
        white_layout.addWidget(select_white_btn)
        
        white_group.setLayout(white_layout)
        self_play_layout.addWidget(white_group)
        
        # Black Model Group
        black_group = QGroupBox("Black Player")
        black_layout = QVBoxLayout()
        
        # Black model display and select button
        self.black_model_label = QLabel(f"Model: {os.path.basename(self.settings['engine']['black_model_path'])}")
        black_layout.addWidget(self.black_model_label)
        
        select_black_btn = QPushButton('Select Model')
        select_black_btn.clicked.connect(lambda: self.select_model_file('black'))
        black_layout.addWidget(select_black_btn)
        
        black_group.setLayout(black_layout)
        self_play_layout.addWidget(black_group)
        
        # Self-Play Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()
        
        # Move delay control
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel('Move Delay (ms):'))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 5000)
        self.delay_spinbox.setValue(500)  # Default 500ms delay
        self.delay_spinbox.setSingleStep(100)
        delay_layout.addWidget(self.delay_spinbox)
        controls_layout.addLayout(delay_layout)
        
        # Start/Stop button
        self.self_play_btn = QPushButton('Start Self-Play')
        self.self_play_btn.clicked.connect(self.toggle_self_play)
        controls_layout.addWidget(self.self_play_btn)
        
        controls_group.setLayout(controls_layout)
        self_play_layout.addWidget(controls_group)
        
        # Add spacer at the bottom
        self_play_layout.addStretch()
        
        self_play_tab.setLayout(self_play_layout)
        tab_widget.addTab(self_play_tab, "Self-Play")
        
        side_layout.addWidget(tab_widget)
        
        # Button layouts for main controls
        button_layout = QHBoxLayout()
        
        # New Game button
        new_game_btn = QPushButton('New Game')
        new_game_btn.clicked.connect(self.new_game)
        button_layout.addWidget(new_game_btn)
        
        # Switch Sides button
        self.switch_sides_btn = QPushButton('Switch to Black')
        self.switch_sides_btn.clicked.connect(self.switch_sides)
        button_layout.addWidget(self.switch_sides_btn)
        
        side_layout.addLayout(button_layout)
        
        # Undo/Redo/Hint buttons
        control_layout = QHBoxLayout()
        
        # Undo button
        self.undo_btn = QPushButton('Undo')
        self.undo_btn.clicked.connect(self.undo_move)
        self.undo_btn.setEnabled(False)
        control_layout.addWidget(self.undo_btn)
        
        # Redo button
        self.redo_btn = QPushButton('Redo')
        self.redo_btn.clicked.connect(self.redo_move)
        self.redo_btn.setEnabled(False)
        control_layout.addWidget(self.redo_btn)
        
        # Hint button
        self.hint_btn = QPushButton('Hint')
        self.hint_btn.clicked.connect(self.show_hint)
        control_layout.addWidget(self.hint_btn)
        
        side_layout.addLayout(control_layout)
        
        side_panel.setLayout(side_layout)
        layout.addWidget(side_panel)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.resize(1200, 800)
        
        # Add self-play timer
        self.self_play_timer = None
        self.is_self_playing = False
    
    def switch_sides(self):
        self.playing_as_white = not self.playing_as_white
        self.switch_sides_btn.setText('Switch to Black' if self.playing_as_white else 'Switch to White')
        self.color_label.setText(f'Playing as: {"White" if self.playing_as_white else "Black"}')
        self.board_widget.flip_board(not self.playing_as_white)  # Flip board when playing as Black
        self.new_game()
    
    def new_game(self):
        self.board_widget.board = chess.Board()
        self.board_widget.update_board()
        self.move_history.clear()
        self.eval_label.setText('Evaluation: 0.0')
        self.hint_label.setText('')
        self.move_stack.clear()
        self.redo_stack.clear()
        self.hint_move = None
        self.update_button_states()
        
        # If playing as Black, make AI move first
        if not self.playing_as_white:
            self.make_ai_move()
    
    def make_ai_move(self):
        # Use appropriate engine based on current turn
        engine = self.white_engine if self.board_widget.board.turn == chess.WHITE else self.black_engine
        value, best_move, move_probs = engine.evaluate_position(self.board_widget.board)
        self.eval_label.setText(f'Evaluation: {value:.3f}')
        
        if best_move:
            # Store move text and algebraic notation before making the move
            ai_move_text = self.board_widget.board.san(best_move)
            ai_move_uci = best_move.uci()
            # Make the move
            self.board_widget.board.push(best_move)
            # Add AI move to stack
            self.move_stack.append(best_move)
            # Update history with stored text and algebraic notation
            prefix = "White: " if self.board_widget.board.turn == chess.BLACK else "Black: "
            self.move_history.append(f"{prefix}{ai_move_text} ({ai_move_uci})\n")
            self.board_widget.update_board()
            return True
        return False
    
    def show_hint(self):
        if not self.board_widget.board.is_game_over() and self.board_widget.board.turn == (chess.WHITE if self.playing_as_white else chess.BLACK):
            # Use appropriate engine based on current turn
            engine = self.white_engine if self.board_widget.board.turn == chess.WHITE else self.black_engine
            value, best_move, move_probs = engine.evaluate_position(self.board_widget.board)
            if best_move:
                move_text = self.board_widget.board.san(best_move)
                self.hint_label.setText(f'Suggested move: {move_text}')
                self.hint_move = best_move
                
                # Get the source and target squares
                from_square = best_move.from_square
                to_square = best_move.to_square
                
                # Convert to board coordinates based on orientation
                if self.board_widget.flipped:
                    from_row = chess.square_rank(from_square)
                    from_col = 7 - chess.square_file(from_square)
                    to_row = chess.square_rank(to_square)
                    to_col = 7 - chess.square_file(to_square)
                else:
                    from_row = 7 - chess.square_rank(from_square)
                    from_col = chess.square_file(from_square)
                    to_row = 7 - chess.square_rank(to_square)
                    to_col = chess.square_file(to_square)
                
                # Update all squares with current theme colors
                for row in range(8):
                    for col in range(8):
                        square = self.board_widget.squares[row][col]
                        base_color = self.board_widget._get_square_color(row, col)
                        if (row, col) in [(from_row, from_col), (to_row, to_col)]:
                            # Highlight hint squares using the last move highlight color
                            square.setStyleSheet(
                                f"background-color: {base_color}; border: 2px solid {self.settings['visual']['highlight_colors']['last_move']};"
                            )
                        else:
                            square.setStyleSheet(f"background-color: {base_color};")
    
    def update_button_states(self):
        self.undo_btn.setEnabled(len(self.move_stack) > 0)
        self.redo_btn.setEnabled(len(self.redo_stack) > 0)
        self.hint_btn.setEnabled(
            not self.board_widget.board.is_game_over() and 
            self.board_widget.board.turn == (chess.WHITE if self.playing_as_white else chess.BLACK)
        )
    
    def on_player_move(self, board_before_move, move_data):
        move, move_text = move_data
        # Verify it's the player's turn using board state before move
        is_player_turn = (board_before_move.turn == chess.WHITE) == self.playing_as_white
        if not is_player_turn:
            # Undo the move in the board
            self.board_widget.board = board_before_move.copy()
            self.board_widget.update_board()
            return
        
        # Make the player's move on a fresh board copy
        self.board_widget.board = board_before_move.copy()
        move_uci = move.uci()  # Get algebraic notation
        self.board_widget.board.push(move)
        self.board_widget.update_board()
        
        # Clear redo stack when a new move is made
        self.redo_stack.clear()
        # Add move to stack
        self.move_stack.append(move)
        # Update move history with move text and algebraic notation
        prefix = "White: " if self.playing_as_white else "Black: "
        self.move_history.append(f"{prefix}{move_text} ({move_uci})")
        
        if not self.board_widget.board.is_game_over():
            # AI's turn
            if self.make_ai_move() and not self.board_widget.board.is_game_over():
                self.update_button_states()
        
        if self.board_widget.board.is_game_over():
            result = self.board_widget.board.result()
            self.move_history.append(f"\nGame Over! Result: {result}")
        
        self.update_button_states()
    
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
            move_uci = player_move.uci()
            self.board_widget.board.push(player_move)
            prefix = "White: " if self.playing_as_white else "Black: "
            self.move_history.append(f"{prefix}{move_text} ({move_uci})")
            
            # Redo AI move
            ai_move = self.redo_stack.pop()
            self.move_stack.append(ai_move)
            move_text = self.board_widget.board.san(ai_move)
            move_uci = ai_move.uci()
            self.board_widget.board.push(ai_move)
            prefix = "Black: " if self.playing_as_white else "White: "
            self.move_history.append(f"{prefix}{move_text} ({move_uci})\n")
            
            self.board_widget.update_board()
            self.update_button_states()
            
            # Update evaluation
            value, _, _ = self.engine.evaluate_position(self.board_widget.board)
            self.eval_label.setText(f'Evaluation: {value:.3f}')
    
    def toggle_self_play(self):
        """Toggle AI self-play mode."""
        if not self.self_play_timer:
            # Create timer if it doesn't exist
            from PyQt6.QtCore import QTimer
            self.self_play_timer = QTimer()
            self.self_play_timer.timeout.connect(self.make_self_play_move)
        
        if not self.is_self_playing:
            # Start self-play
            self.is_self_playing = True
            self.self_play_btn.setText('Stop Self-Play')
            self.switch_sides_btn.setEnabled(False)
            self.hint_btn.setEnabled(False)
            self.delay_spinbox.setEnabled(False)
            self.undo_btn.setEnabled(False)
            self.redo_btn.setEnabled(False)
            
            # Start timer with current delay
            self.self_play_timer.start(self.delay_spinbox.value())
            
            # Make first move if it's AI's turn
            if not self.board_widget.board.is_game_over():
                self.make_self_play_move()
        else:
            # Stop self-play
            self.stop_self_play()
    
    def stop_self_play(self):
        """Stop AI self-play mode."""
        if self.self_play_timer:
            self.self_play_timer.stop()
        self.is_self_playing = False
        self.self_play_btn.setText('Start Self-Play')
        self.switch_sides_btn.setEnabled(True)
        self.hint_btn.setEnabled(True)
        self.delay_spinbox.setEnabled(True)
        self.update_button_states()
    
    def make_self_play_move(self):
        """Make a move in self-play mode."""
        if not self.board_widget.board.is_game_over():
            # Use appropriate engine based on current turn
            engine = self.white_engine if self.board_widget.board.turn == chess.WHITE else self.black_engine
            value, best_move, move_probs = engine.evaluate_position(self.board_widget.board)
            
            if best_move:
                # Store move text before making the move
                move_text = self.board_widget.board.san(best_move)
                move_uci = best_move.uci()
                
                # Make the move
                self.board_widget.board.push(best_move)
                self.move_stack.append(best_move)
                
                # Update move history
                prefix = "White: " if self.board_widget.board.turn == chess.BLACK else "Black: "
                self.move_history.append(f"{prefix}{move_text} ({move_uci})\n")
                
                # Update evaluation
                self.eval_label.setText(f'Evaluation: {value:.3f}')
                
                # Update display
                self.board_widget.update_board()
                
                # Stop if game is over
                if self.board_widget.board.is_game_over():
                    result = self.board_widget.board.result()
                    self.move_history.append(f"\nGame Over! Result: {result}")
                    self.stop_self_play()
        else:
            self.stop_self_play()

def main():
    app = QApplication(sys.argv)
    
    # Create pieces directory and download images if needed
    if not os.path.exists('pieces'):
        os.makedirs('pieces')
        # Here you would need to add code to download or copy piece images
        print("Please add chess piece images to the 'pieces' directory")
        return
    
    engine_path = "models/model_epoch_20.pt"  # Updated path to use local directory
    gui = ChessGUI(engine_path)
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 
# Chess AI: Deep Learning-based Chess Engine

This project implements a deep learning-based chess engine that can play chess, evaluate positions, and suggest moves. It includes functionality for training the model on chess game data, playing interactive games, and analyzing chess positions.

The Chess AI uses a neural network architecture to learn chess strategies from a large dataset of chess games. It can be trained on PGN (Portable Game Notation) files containing chess games, and then used for inference to evaluate positions and suggest moves.

## Repository Structure

```
.
├── canvas-update.py
├── config.py
├── data
│   ├── chess_dataset.py
│   └── download_games.py
├── download_pieces.py
├── example.py
├── gui.py
├── inference.py
├── models
│   └── chess_model.py
├── requirements.txt
├── setup_flash_drive.py
├── train_pipeline.py
├── train.py
└── utils
    └── board_utils.py
```

### Key Files:
- `train.py`: Main script for training the chess model
- `inference.py`: Script for running inference with the trained model
- `config.py`: Configuration file for project paths and settings
- `models/chess_model.py`: Definition of the neural network architecture
- `data/chess_dataset.py`: Dataset class for loading and processing chess games
- `data/download_games.py`: Script for downloading and preprocessing chess game data
- `utils/board_utils.py`: Utility functions for chess board representation and move encoding

## Usage Instructions

### Installation

1. Ensure you have Python 3.7+ installed.
2. Clone this repository:
   ```
   git clone <repository_url>
   cd ChessAI
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Getting Started

1. Download chess game data:
   ```
   python data/download_games.py
   ```

2. Train the model:
   ```
   python train.py --pgn_files games/lichess_games_filtered.pgn
   ```

3. Run inference:
   ```
   python inference.py --model_path checkpoints/model_epoch_10.pt
   ```

### Configuration

- Adjust training parameters in `train.py` using command-line arguments.
- Modify model architecture in `models/chess_model.py`.
- Configure data paths and project settings in `config.py`.

### Common Use Cases

1. Analyze a specific position:
   ```
   python inference.py --model_path checkpoints/model_epoch_10.pt --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
   ```

2. Play an interactive game against the AI:
   ```
   python inference.py --model_path checkpoints/model_epoch_10.pt --interactive
   ```

3. Train on multiple PGN files:
   ```
   python train.py --pgn_files games/file1.pgn games/file2.pgn --epochs 20 --batch_size 512
   ```

### Testing & Quality

- Run unit tests (if available) using:
  ```
  python -m unittest discover tests
  ```

### Troubleshooting

1. Issue: CUDA out of memory error during training
   - Reduce batch size: `python train.py --batch_size 128`
   - Use CPU if GPU memory is insufficient: `python train.py --cpu`

2. Issue: Slow data loading
   - Increase number of workers: `python train.py --num_workers 8`
   - Ensure PGN files are not corrupted

3. Issue: Model not improving during training
   - Check learning rate: `python train.py --learning_rate 0.0001`
   - Increase number of epochs: `python train.py --epochs 50`

### Debugging

- Enable debug mode in `train.py` and `inference.py` by adding `--debug` flag
- Check log files in the `logs` directory for detailed output
- Use PyTorch's profiler to identify performance bottlenecks:
  ```python
  with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
      # Your code here
  print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))
  ```

## Data Flow

The Chess AI project follows this general data flow:

1. Data Acquisition: Download chess games using `data/download_games.py`
2. Data Preprocessing: Filter and prepare games for training
3. Model Training: `train.py` loads data, trains the model, and saves checkpoints
4. Inference: `inference.py` loads a trained model and evaluates chess positions

```
[Data Source] -> [Preprocessing] -> [Training] -> [Model] -> [Inference] -> [Evaluation]
     |                 |               |            |           |             |
     v                 v               v            v           v             v
  PGN Files    Filtered Games    ChessDataset   ChessNet   ChessEngine    Move Suggestions
```

Note: The GUI component (`gui.py`) interacts with the inference pipeline to provide a user interface for playing against the AI or analyzing positions.

## Deployment

To deploy the Chess AI:

1. Ensure all dependencies are installed on the target system
2. Copy the trained model checkpoint to the deployment environment
3. Use `inference.py` with appropriate arguments to run the chess engine

For web-based deployment, consider wrapping the `ChessEngine` class in a web framework like Flask or FastAPI.

## Infrastructure

The project uses a simple file-based structure without dedicated infrastructure components. Key configuration elements include:

- External HDD path configuration in `config.py`
- Project directories (data, games, models, checkpoints) defined in `config.py`
- Dependencies listed in `requirements.txt`

Ensure the external HDD is properly mounted and accessible for data storage and model checkpoints.
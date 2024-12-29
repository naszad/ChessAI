# Chess AI with Deep Learning

A deep learning system for chess position evaluation and move prediction, implemented in PyTorch. The system uses a convolutional neural network with dual heads for position evaluation and move prediction.

## Features

- Board position encoding into a multi-channel representation
- Custom CNN architecture with value and policy heads
- Training pipeline for learning from GM games
- Move suggestion system

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

- `models/` - Neural network architecture
- `data/` - Data processing and dataset classes
- `utils/` - Utility functions for board encoding and move processing
- `train.py` - Training script
- `inference.py` - Move suggestion and position evaluation

## Usage

More details coming soon as the project develops.
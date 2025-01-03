import torch
from torch.utils.data import DataLoader
import torch.optim as optim
from tqdm import tqdm
import argparse
import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import CHECKPOINTS_DIR
from models.chess_model import ChessNet, value_loss_fn, policy_loss_fn
from data.chess_dataset import ChessDataset

def train(args):
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"Using device: {device}")
    
    # Create model
    model = ChessNet(num_res_blocks=args.num_res_blocks)
    
    # Create optimizer (we'll load state later if resuming)
    optimizer = optim.Adam(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay
    )
    
    # Create scheduler (we'll load state later if resuming)
    scheduler = optim.lr_scheduler.StepLR(
        optimizer,
        step_size=args.lr_step,
        gamma=args.lr_gamma
    )
    
    # Load checkpoint if resuming
    start_epoch = 0
    if args.resume_from:
        print(f"Loading checkpoint from {args.resume_from}")
        checkpoint = torch.load(args.resume_from, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch']
        print(f"Resuming from epoch {start_epoch}")
    
    model = model.to(device)
    
    # Load dataset
    print("\nLoading dataset...")
    print("PGN files:")
    for pgn_file in args.pgn_files:
        print(f"  - {pgn_file}")
        if not os.path.exists(pgn_file):
            print(f"[ERROR] File not found: {pgn_file}")
            return
        
    dataset = ChessDataset(
        pgn_files=args.pgn_files,
        max_positions=args.max_positions
    )
    print(f"Dataset size: {len(dataset):,} positions")
    
    if len(dataset) == 0:
        print("[ERROR] No positions loaded from dataset")
        return
    
    # Create data loader
    print("\nCreating data loader...")
    print("Using single-threaded data loading for debugging")
    
    try:
        dataloader = DataLoader(
            dataset,
            batch_size=args.batch_size,
            shuffle=True,
            num_workers=0,  # Single-threaded
            pin_memory=False  # Disable pin_memory when using CPU
        )
        print(f"Number of batches: {len(dataloader):,}")
        
        # Try loading first batch to verify data loading works
        print("\nTesting data loading...")
        test_iter = iter(dataloader)
        try:
            positions, policies, values = next(test_iter)
            print(f"Successfully loaded first batch:")
            print(f"  Positions shape: {positions.shape}")
            print(f"  Policies shape: {policies.shape}")
            print(f"  Values shape: {values.shape}")
        except Exception as e:
            print(f"Error loading first batch: {str(e)}")
            raise e
        
        # Training loop
        print("\nStarting training...")
        print(f"Training from epoch {start_epoch + 1} to {start_epoch + args.epochs}")
        
        for epoch in range(start_epoch, start_epoch + args.epochs):
            print(f"\nStarting epoch {epoch + 1}...")
            model.train()
            total_loss = 0
            total_value_loss = 0
            total_policy_loss = 0
            num_batches = 0
            
            progress_bar = tqdm(
                dataloader,
                desc=f"Epoch {epoch+1}/{start_epoch + args.epochs}",
                ncols=100,
                leave=True
            )
            
            try:
                for batch_idx, (positions, policies, values) in enumerate(progress_bar):
                    if batch_idx == 0:
                        print(f"First batch loaded successfully")
                    
                    # Move data to device
                    positions = positions.to(device)
                    policies = policies.to(device)
                    values = values.to(device)
                    
                    # Forward pass
                    pred_values, pred_policies = model(positions)
                    
                    # Compute losses
                    v_loss = value_loss_fn(pred_values, values)
                    p_loss = policy_loss_fn(pred_policies, policies)
                    loss = v_loss + p_loss
                    
                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    # Update statistics
                    total_loss += loss.item()
                    total_value_loss += v_loss.item()
                    total_policy_loss += p_loss.item()
                    num_batches += 1
                    
                    # Update progress bar
                    progress_bar.set_postfix({
                        'loss': f'{total_loss / num_batches:.4f}',
                        'v_loss': f'{total_value_loss / num_batches:.4f}',
                        'p_loss': f'{total_policy_loss / num_batches:.4f}'
                    })
                    
                    if batch_idx % 100 == 0:
                        print(f"\nBatch {batch_idx}/{len(dataloader)}, "
                              f"Loss: {total_loss / num_batches:.4f}, "
                              f"Value Loss: {total_value_loss / num_batches:.4f}, "
                              f"Policy Loss: {total_policy_loss / num_batches:.4f}")
                
            except Exception as e:
                print(f"\nError during training: {str(e)}")
                raise e
            
            # Step learning rate scheduler
            scheduler.step()
            
            # Save checkpoint
            if (epoch + 1) % args.save_every == 0:
                checkpoint_path = os.path.join(CHECKPOINTS_DIR, f"model_epoch_{epoch+1}.pt")
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict(),
                    'loss': total_loss / num_batches,
                }, checkpoint_path)
                print(f"\nSaved checkpoint to {checkpoint_path}")
    
    except Exception as e:
        print(f"\nError setting up training: {str(e)}")
        raise e

def main():
    parser = argparse.ArgumentParser(description="Train chess model")
    
    # Data arguments
    parser.add_argument('--pgn_files', nargs='+', required=True,
                        help='List of PGN files to train on')
    parser.add_argument('--max_positions', type=int, default=None,
                        help='Maximum number of positions to load (for debugging)')
    
    # Model arguments
    parser.add_argument('--num_res_blocks', type=int, default=8,
                        help='Number of residual blocks in the model')
    
    # Training arguments
    parser.add_argument('--batch_size', type=int, default=256,
                        help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of epochs to train')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                        help='Initial learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-4,
                        help='Weight decay (L2 regularization)')
    parser.add_argument('--lr_step', type=int, default=5,
                        help='Number of epochs between learning rate decay')
    parser.add_argument('--lr_gamma', type=float, default=0.1,
                        help='Learning rate decay factor')
    
    # System arguments
    parser.add_argument('--num_workers', type=int, default=4,
                        help='Number of data loading workers')
    parser.add_argument('--cpu', action='store_true',
                        help='Force CPU training')
    parser.add_argument('--save_every', type=int, default=1,
                        help='Save checkpoint every N epochs')
    
    # Checkpoint arguments
    parser.add_argument('--resume_from', type=str,
                        help='Path to checkpoint to resume from')
    
    args = parser.parse_args()
    
    train(args)

if __name__ == '__main__':
    main()
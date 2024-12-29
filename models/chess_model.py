import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)
    
    def forward(self, x):
        identity = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += identity
        out = F.relu(out)
        return out

class ChessNet(nn.Module):
    def __init__(self, num_channels=14, num_res_blocks=8):
        """
        Chess neural network with value and policy heads.
        
        Args:
            num_channels: Number of input channels (14 in our encoding)
            num_res_blocks: Number of residual blocks in the network
        """
        super(ChessNet, self).__init__()
        
        # Initial convolution block
        self.conv_input = nn.Sequential(
            nn.Conv2d(num_channels, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU()
        )
        
        # Residual blocks
        self.res_blocks = nn.ModuleList([
            ResidualBlock(256) for _ in range(num_res_blocks)
        ])
        
        # Value head
        self.value_head = nn.Sequential(
            nn.Conv2d(256, 1, kernel_size=1),
            nn.BatchNorm2d(1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Tanh()  # Output in [-1, 1]
        )
        
        # Policy head (outputs logits for 4096 possible moves)
        self.policy_head = nn.Sequential(
            nn.Conv2d(256, 256, kernel_size=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(256 * 64, 1024),
            nn.ReLU(),
            nn.Linear(1024, 4096)  # Raw logits for each possible move
        )
    
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, num_channels, 8, 8)
            
        Returns:
            tuple (value, policy):
                value: tensor of shape (batch_size, 1) with position evaluations
                policy: tensor of shape (batch_size, 4096) with move probabilities
        """
        # Common layers
        x = self.conv_input(x)
        for res_block in self.res_blocks:
            x = res_block(x)
        
        # Value head
        value = self.value_head(x)
        
        # Policy head
        policy = self.policy_head(x)
        
        return value, policy

def value_loss_fn(pred_values, target_values):
    """
    Compute MSE loss for the value head.
    """
    return F.mse_loss(pred_values, target_values)

def policy_loss_fn(policy_logits, target_moves):
    """
    Compute cross-entropy loss for the policy head.
    
    Args:
        policy_logits: Raw logits from the policy head
        target_moves: One-hot encoded target moves
    """
    return F.cross_entropy(policy_logits, torch.argmax(target_moves, dim=1))
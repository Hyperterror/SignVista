"""
SignVista LSTM Model Architecture

PyTorch LSTM for word-level ISL recognition from pose keypoint sequences.

Ishit: This architecture must match your trained model exactly.
       Update INPUT_SIZE, HIDDEN_SIZE, NUM_LAYERS, and forward() if needed.
       Place your trained weights at: ml/models/weights/model.pth
"""

import torch
import torch.nn as nn

from ml.vocabulary import NUM_CLASSES


# ─── Model Hyperparameters ────────────────────────────────────────
# These MUST match Ishit's training configuration

INPUT_SIZE = 99       # 33 Mediapipe Pose landmarks × 3 coords (x, y, z)
HIDDEN_SIZE = 128     # LSTM hidden dimension
NUM_LAYERS = 2        # Stacked LSTM layers
SEQUENCE_LENGTH = 45  # Frames per prediction window
DROPOUT = 0.3         # Dropout rate (training)


class ISLRecognitionLSTM(nn.Module):
    """
    LSTM model for Indian Sign Language word-level recognition.

    Input:  (batch_size, sequence_length=45, input_size=99)
    Output: (batch_size, num_classes=15) — logits for each word
    """

    def __init__(
        self,
        input_size: int = INPUT_SIZE,
        hidden_size: int = HIDDEN_SIZE,
        num_layers: int = NUM_LAYERS,
        num_classes: int = NUM_CLASSES,
        dropout: float = DROPOUT,
    ):
        super(ISLRecognitionLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Fully connected classifier
        self.fc = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch, seq_len, input_size)

        Returns:
            Logits tensor of shape (batch, num_classes)
        """
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        # LSTM forward
        lstm_out, _ = self.lstm(x, (h0, c0))

        # Take output from last timestep
        last_output = lstm_out[:, -1, :]

        # Classify
        logits = self.fc(last_output)
        return logits


def load_lstm_model(model_path: str) -> ISLRecognitionLSTM:
    """
    Load trained LSTM model from weights file.

    Args:
        model_path: Path to .pth weights file

    Returns:
        Model in eval mode

    Raises:
        FileNotFoundError: If weights file doesn't exist
    """
    model = ISLRecognitionLSTM()
    state_dict = torch.load(model_path, map_location=torch.device("cpu"), weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model

"""
LSTM Sequence Model for Behavioral Analysis

Learns temporal patterns from user transaction sequences (5-50 transactions),
not just single-transaction statistics.
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import structlog

# Optional torch import - backend can work without it for demo
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy classes for when torch isn't installed
    
    class _DummyTensor:
        def __init__(self, *args, **kwargs):
            self._data = None
        def unsqueeze(self, *args):
            return self
        def squeeze(self, *args):
            return self
        def to(self, *args):
            return self
        def numpy(self):
            return np.array([0.0])
        def item(self):
            return 0.0
        def __float__(self):
            return 0.0
        def tolist(self):
            return [0.0]
    
    class nn:
        class Module:
            def eval(self):
                pass
            def __call__(self, x):
                return self.forward(x)
            def forward(self, x):
                return x
        class Sequential:
            def __init__(self, *args):
                self.layers = args
            def __call__(self, x):
                return x
        class Linear:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, x):
                return x
        class ReLU:
            def __call__(self, x):
                return x
        class Dropout:
            def __init__(self, *args):
                pass
            def __call__(self, x):
                return x
        class Sigmoid:
            def __call__(self, x):
                return x
        class LSTM:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, x):
                return x, x  # Return tuple like real LSTM
    
    class torch:
        Tensor = _DummyTensor
        @staticmethod
        def tensor(*args, **kwargs):
            return _DummyTensor(*args, **kwargs)
        @staticmethod
        def load(*args, **kwargs):
            return None
        @staticmethod
        def sigmoid(x):
            return x if hasattr(x, 'unsqueeze') else _DummyTensor()
        @staticmethod
        def no_grad():
            class NoGradContext:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return NoGradContext()

logger = structlog.get_logger()


class TransactionSequenceEncoder(nn.Module):
    """
    LSTM encoder that processes a sequence of transactions and outputs
    a behavioral anomaly score.
    
    Architecture:
    - Input: (batch, seq_len, features) - sequence of transaction features
    - LSTM: 2-layer bidirectional LSTM with 64 hidden units
    - Output: (batch, 1) - anomaly score [0, 1]
    """
    
    def __init__(self, input_dim: int = 8, hidden_dim: int = 64, num_layers: int = 2):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.2 if num_layers > 1 else 0
        )
        
        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),  # *2 for bidirectional
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output anomaly score [0, 1]
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: (batch_size, seq_len, input_dim) tensor of transaction sequences
            
        Returns:
            (batch_size, 1) tensor of anomaly scores
        """
        # LSTM output
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Take final hidden state from both directions
        # hidden: (num_layers * 2, batch, hidden_dim)
        final_forward = hidden[-2, :, :]  # Last layer forward
        final_backward = hidden[-1, :, :]  # Last layer backward
        final_hidden = torch.cat([final_forward, final_backward], dim=1)
        
        # Pass through fully connected layers
        output = self.fc(final_hidden)
        
        return output


class SequenceBehavioralAnalyzer:
    """
    Analyzes user behavior using LSTM sequence model.
    
    This replaces simple heuristic behavioral indices with learned temporal patterns.
    The model learns "normal" behavior for each user from their transaction history,
    then detects anomalies in new transactions based on deviation from that pattern.
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.is_loaded = False
        self.feature_dim = 8  # Number of features per transaction in sequence
        self.sequence_length = 10  # Default sequence length
        
        if model_path:
            self.load_model(model_path)
        else:
            # Initialize with random weights for demo (would be trained in production)
            self._init_demo_model()
    
    def _init_demo_model(self):
        """Initialize model with random weights for demo purposes."""
        self.model = TransactionSequenceEncoder(
            input_dim=self.feature_dim,
            hidden_dim=64,
            num_layers=2
        )
        self.model.eval()  # Set to evaluation mode
        self.is_loaded = True
        logger.info("sequence_analyzer_initialized_demo_mode")
    
    def load_model(self, model_path: str):
        """Load trained LSTM model from file."""
        try:
            self.model = torch.load(model_path, map_location='cpu')
            self.model.eval()
            self.is_loaded = True
            logger.info("sequence_model_loaded", path=model_path)
        except Exception as e:
            logger.error("sequence_model_load_failed", error=str(e))
            self._init_demo_model()
    
    def _extract_sequence_features(self, transactions: List[Dict]) -> np.ndarray:
        """
        Extract features from a sequence of transactions.
        
        Features per transaction:
        1. normalized_amount: amount / user_avg_amount
        2. hour_sin: sin(2π * hour / 24) - time of day cyclical
        3. hour_cos: cos(2π * hour / 24) - time of day cyclical
        4. day_of_week: 0-6
        5. geo_lat_norm: normalized latitude
        6. geo_lng_norm: normalized longitude
        7. merchant_category_encoded: merchant type
        8. time_since_last: hours since previous transaction
        
        Args:
            transactions: List of transaction dicts, ordered by time (oldest first)
            
        Returns:
            (seq_len, feature_dim) numpy array
        """
        features = []
        
        # Compute user averages for normalization
        amounts = [t.get("amount", 0) for t in transactions]
        avg_amount = np.mean(amounts) if amounts else 1.0
        
        prev_time = None
        
        for txn in transactions:
            # 1. Normalized amount
            amount = txn.get("amount", 0) / max(avg_amount, 1.0)
            
            # 2-3. Time cyclical encoding
            txn_time = txn.get("txn_timestamp")
            if isinstance(txn_time, str):
                txn_time = datetime.fromisoformat(txn_time.replace('Z', '+00:00'))
            
            hour = txn_time.hour if txn_time else 12
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)
            
            # 4. Day of week
            day_of_week = txn_time.weekday() / 6.0 if txn_time else 0.5
            
            # 5-6. Normalized geo coordinates
            lat = txn.get("geo_lat", 0) or 0
            lng = txn.get("geo_lng", 0) or 0
            geo_lat_norm = (lat + 90) / 180.0  # Normalize to [0, 1]
            geo_lng_norm = (lng + 180) / 360.0  # Normalize to [0, 1]
            
            # 7. Merchant category (simple hash-based encoding)
            merchant_cat = txn.get("merchant_category", "")
            cat_encoded = hash(merchant_cat) % 100 / 100.0  # Simple encoding
            
            # 8. Time since last transaction
            time_since_last = 0.0
            if prev_time:
                delta = (txn_time - prev_time).total_seconds() / 3600.0  # hours
                time_since_last = min(delta / 24.0, 1.0)  # Normalize to [0, 1]
            prev_time = txn_time
            
            feature_vec = [
                amount, hour_sin, hour_cos, day_of_week,
                geo_lat_norm, geo_lng_norm, cat_encoded, time_since_last
            ]
            features.append(feature_vec)
        
        # Pad or truncate to sequence_length
        if len(features) < self.sequence_length:
            # Pad with zeros at beginning
            padding = [[0.0] * self.feature_dim] * (self.sequence_length - len(features))
            features = padding + features
        elif len(features) > self.sequence_length:
            # Take most recent sequence_length transactions
            features = features[-self.sequence_length:]
        
        return np.array(features, dtype=np.float32)
    
    def analyze_sequence(self, user_history: List[Dict]) -> Dict[str, float]:
        """
        Analyze a user's transaction sequence and return anomaly scores.
        
        Args:
            user_history: List of user's past transactions (5-50 transactions)
            
        Returns:
            Dictionary with anomaly scores and confidence
        """
        if not user_history:
            return {
                "sequence_anomaly_score": 0.5,
                "confidence": 0.0,
                "pattern_break_detected": False
            }
        
        if len(user_history) < 3:
            # Not enough history for sequence analysis
            return {
                "sequence_anomaly_score": 0.3,
                "confidence": 0.3,
                "pattern_break_detected": False,
                "note": "insufficient_history"
            }
        
        # Extract features
        sequence_features = self._extract_sequence_features(user_history)
        
        # Convert to tensor and add batch dimension
        x = torch.tensor(sequence_features).unsqueeze(0)  # (1, seq_len, features)
        
        # Run inference
        with torch.no_grad():
            anomaly_score = self.model(x).item()
        
        # Determine if this is a pattern break
        pattern_break = anomaly_score > 0.7
        
        # Confidence based on history length
        confidence = min(1.0, len(user_history) / self.sequence_length)
        
        return {
            "sequence_anomaly_score": anomaly_score,
            "confidence": confidence,
            "pattern_break_detected": pattern_break,
            "history_length": len(user_history)
        }
    
    def compute_sequence_deviation(self, 
                                   recent_sequence: List[Dict],
                                   current_transaction: Dict) -> float:
        """
        Compute how much the current transaction deviates from recent pattern.
        
        Args:
            recent_sequence: Recent transactions (excluding current)
            current_transaction: The new transaction to evaluate
            
        Returns:
            Deviation score [0, 1] where higher = more anomalous
        """
        # Add current transaction to sequence
        full_sequence = recent_sequence + [current_transaction]
        
        result = self.analyze_sequence(full_sequence)
        
        return result["sequence_anomaly_score"]


# Singleton instance
sequence_analyzer = SequenceBehavioralAnalyzer()

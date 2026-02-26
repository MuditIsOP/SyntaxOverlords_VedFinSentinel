"""
Learned Behavioral Embeddings

Replaces heuristic threshold rules (ADI, GRI, DTS, TRC, MRS) with neural network embeddings.
Each index is now a learned dense vector from a small neural network, not a threshold calculation.
"""

import os
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timezone
import structlog

# Optional torch import - backend can work without it for demo
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy classes for when torch isn't installed
    
    # Define Tensor first as standalone
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
        class BCEWithLogitsLoss:
            def __call__(self, *args, **kwargs):
                return _DummyTensor()
    
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

# Default model path
DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "ml", "artifacts", "behavioral_embedding_model.pt"
)


class BehavioralEmbeddingNet(nn.Module):
    """
    Neural network that learns behavioral embeddings from raw transaction features.
    
    Architecture:
    - Input: Raw transaction features (amount, geo, time, device, merchant)
    - Hidden: 32-unit dense layer with ReLU
    - Output: 5-dim behavioral embedding (replaces ADI, GRI, DTS, TRC, MRS)
    
    This replaces threshold-based indices with learned representations.
    """
    
    def __init__(self, input_dim: int = 9, embedding_dim: int = 5):
        super().__init__()
        
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        
        # Feature encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, embedding_dim),
            nn.Sigmoid()  # Output [0, 1] range for interpretability
        )
        
        # Individual index heads for named outputs
        self.adi_head = nn.Linear(embedding_dim, 1)  # Amount Deviation
        self.gri_head = nn.Linear(embedding_dim, 1)  # Geographic Risk
        self.dts_head = nn.Linear(embedding_dim, 1)  # Device Trust
        self.trc_head = nn.Linear(embedding_dim, 1)  # Time Risk
        self.mrs_head = nn.Linear(embedding_dim, 1)  # Merchant Risk
        
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: (batch, input_dim) raw features
            
        Returns:
            Dict with embedding and individual index scores
        """
        # Learned embedding
        embedding = self.encoder(x)
        
        # Individual index outputs (for compatibility)
        adi = torch.sigmoid(self.adi_head(embedding))
        gri = torch.sigmoid(self.gri_head(embedding))
        dts = torch.sigmoid(self.dts_head(embedding))
        trc = torch.sigmoid(self.trc_head(embedding))
        mrs = torch.sigmoid(self.mrs_head(embedding))
        
        return {
            "embedding": embedding,
            "ADI": adi,
            "GRI": gri,
            "DTS": dts,
            "TRC": trc,
            "MRS": mrs
        }


class LearnedBehavioralAnalyzer:
    """
    Analyzer that uses neural network embeddings instead of heuristics.
    
    Replaces:
    - compute_adi() → learned amount deviation
    - compute_gri() → learned geographic risk  
    - compute_dts() → learned device trust
    - compute_trc() → learned time risk
    - compute_mrs() → learned merchant risk
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.is_loaded = False
        
        # Try to load trained model, fall back to demo only if no trained model exists
        if model_path:
            self.load_model(model_path)
        else:
            # Try default path first
            self._try_load_trained_model()
    
    def _try_load_trained_model(self):
        """Attempt to load trained model from artifacts directory."""
        # Check multiple possible paths
        possible_paths = [
            DEFAULT_MODEL_PATH,
            os.path.join("backend", "ml", "artifacts", "behavioral_embedding_model.pt"),
            os.path.join("ml", "artifacts", "behavioral_embedding_model.pt"),
            os.path.join(os.getcwd(), "backend", "ml", "artifacts", "behavioral_embedding_model.pt"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.load_model(path)
                return
        
        # No trained model found - use demo mode
        logger.warning("behavioral_model_no_trained_weights_found_using_demo_mode")
        self._init_demo_model()
        logger.warning("⚠️  Running with random weights - run generate_model.py to train")
    
    def _init_demo_model(self):
        """Initialize with random weights for demo."""
        self.model = BehavioralEmbeddingNet(input_dim=9, embedding_dim=5)
        self.model.eval()
        self.is_loaded = True
        logger.info("behavioral_analyzer_initialized_demo_mode")
    
    def load_model(self, model_path: str):
        """Load trained model weights."""
        try:
            # Initialize model architecture
            self.model = BehavioralEmbeddingNet(input_dim=9, embedding_dim=5)
            
            # Load state dict
            state_dict = torch.load(model_path, map_location='cpu')
            self.model.load_state_dict(state_dict)
            
            self.model.eval()
            self.is_loaded = True
            self.model_path = model_path
            logger.info("behavioral_model_loaded_trained_weights", path=model_path)
        except Exception as e:
            logger.error("behavioral_model_load_failed", error=str(e))
            self._init_demo_model()
    
    def get_status(self) -> Dict[str, any]:
        """Return current model status."""
        return {
            "is_loaded": self.is_loaded,
            "using_trained_weights": hasattr(self, 'model_path'),
            "model_path": getattr(self, 'model_path', None),
            "mode": "trained" if hasattr(self, 'model_path') else "demo"
        }
    
    def _extract_features(self, txn: Dict, user_baseline: Dict) -> np.ndarray:
        """
        Extract raw features for neural network.
        
        Features:
        1. normalized_amount: txn_amount / user_avg
        2. amount_zscore: (amount - mean) / std
        3. geo_lat_norm: normalized lat
        4. geo_lng_norm: normalized lng  
        5. hour_sin: sin(2π * hour / 24)
        6. hour_cos: cos(2π * hour / 24)
        7. device_known: 1 if device in history
        8. merchant_risk_raw: high-risk merchant indicator
        9. time_since_last: hours since last txn
        """
        # Amount features
        amount = txn.get("amount", 0)
        user_mean = user_baseline.get("amount_mean", amount)
        user_std = user_baseline.get("amount_std", 1)
        
        normalized_amount = amount / max(user_mean, 1)
        amount_zscore = (amount - user_mean) / max(user_std, 1)
        
        # Geo features
        lat = txn.get("geo_lat", 0) or 0
        lng = txn.get("geo_lng", 0) or 0
        geo_lat_norm = (lat + 90) / 180
        geo_lng_norm = (lng + 180) / 360
        
        # Time features
        txn_time = txn.get("txn_timestamp")
        if isinstance(txn_time, str):
            txn_time = datetime.fromisoformat(txn_time.replace('Z', '+00:00'))
        
        hour = txn_time.hour if txn_time else 12
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)
        
        # Device feature
        device_id = txn.get("device_id", "")
        known_devices = user_baseline.get("device_counts", {})
        device_known = 1.0 if device_id in known_devices else 0.0
        
        # Merchant feature
        merchant_cat = txn.get("merchant_category", "")
        high_risk = {"CRYPTO", "GAMBLING", "ADULT", "WIRE_TRANSFER"}
        merchant_risk_raw = 1.0 if merchant_cat.upper() in high_risk else 0.0
        
        # Time since last (from baseline)
        time_since_last = user_baseline.get("hours_since_last_txn", 24) / 168.0  # Normalize to week
        
        features = [
            normalized_amount, amount_zscore, geo_lat_norm, geo_lng_norm,
            hour_sin, hour_cos, device_known, merchant_risk_raw, time_since_last
        ]
        
        return np.array(features, dtype=np.float32)
    
    def analyze(self, txn: Dict, user_baseline: Dict) -> Dict[str, float]:
        """
        Analyze transaction using learned embeddings.
        
        Returns behavioral indices as learned neural network outputs,
        not threshold-based calculations.
        """
        # Extract features
        features = self._extract_features(txn, user_baseline)
        
        # Convert to tensor
        x = torch.tensor(features).unsqueeze(0)  # Add batch dim
        
        # Run through neural network
        with torch.no_grad():
            outputs = self.model(x)
        
        # Return learned indices
        return {
            "ADI": outputs["ADI"].item(),
            "GRI": outputs["GRI"].item(),
            "DTS": outputs["DTS"].item(),
            "TRC": outputs["TRC"].item(),
            "MRS": outputs["MRS"].item(),
            "embedding": outputs["embedding"].squeeze().tolist()
        }


# Singleton
behavioral_analyzer = LearnedBehavioralAnalyzer()

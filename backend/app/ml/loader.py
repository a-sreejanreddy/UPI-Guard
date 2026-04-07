"""
app/ml/loader.py — ML model loader singleton

Loads mlp_model.h5 + scaler.pkl once at FastAPI startup via lifespan.
All route handlers call `get_model_loader().predict(features)` to get fraud_score.

Usage:
    # In lifespan startup:
    ml = get_model_loader()
    ml.load(settings.MODEL_PATH, settings.SCALER_PATH)

    # In route handler:
    score = get_model_loader().predict([hour, day, month, year, cat, amount, age, state, zip])
"""
import hashlib
import os
import pickle
import pathlib
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# Suppress TensorFlow verbose output
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

_EXPECTED_FEATURE_COUNT = 9


@dataclass
class ModelLoader:
    """
    Wraps the Keras MLP model and StandardScaler.
    Designed to be instantiated once and reused across all requests.
    """
    model:   Optional[object] = field(default=None, repr=False)
    scaler:  Optional[object] = field(default=None, repr=False)
    _loaded: bool = field(default=False, repr=False)

    def load(self, model_path: str, scaler_path: str) -> None:
        """
        Load model and scaler from disk.
        Raises FileNotFoundError if either artifact is missing.
        """
        import tensorflow as tf

        model_p  = pathlib.Path(model_path)
        scaler_p = pathlib.Path(scaler_path)

        if not model_p.exists():
            raise FileNotFoundError(
                f"MLP model not found at {model_p.resolve()}. "
                "Run: cd backend && python -m ml_pipeline.train"
            )
        if not scaler_p.exists():
            raise FileNotFoundError(
                f"Scaler not found at {scaler_p.resolve()}. "
                "Run: cd backend && python -m ml_pipeline.train"
            )

        self.model  = tf.keras.models.load_model(str(model_p))

        # Verify scaler checksum before deserializing (prevents loading tampered artifacts)
        digest_path = scaler_p.with_suffix(".pkl.sha256")
        scaler_bytes = scaler_p.read_bytes()
        actual_digest = hashlib.sha256(scaler_bytes).hexdigest()

        if digest_path.exists():
            expected_digest = digest_path.read_text(encoding="utf-8").strip()
            if actual_digest != expected_digest:
                raise ValueError(
                    f"Scaler artifact checksum mismatch!\n"
                    f"  Expected : {expected_digest}\n"
                    f"  Actual   : {actual_digest}\n"
                    f"Do not use — re-run ml_pipeline/train.py to regenerate clean artifacts."
                )
            print(f"[ML] Scaler checksum verified (SHA-256 OK)")
        else:
            # First run: write the digest so future startups can verify integrity
            digest_path.write_text(actual_digest, encoding="utf-8")
            print(f"[ML] Scaler checksum stored  : {digest_path.name}")

        with open(scaler_p, "rb") as f:
            self.scaler = pickle.load(f)

        self._loaded = True
        print(f"[ML] Loaded model  : {model_p.name}  (input shape: {self.model.input_shape})")
        print(f"[ML] Loaded scaler : {scaler_p.name}")

    def predict(self, features: list) -> float:
        """
        Run fraud inference on a single transaction's feature vector.

        Parameters
        ----------
        features : list of 9 floats/ints in order:
            [hour, day, month, year, merchant_category, amount, user_age, state_code, zip_prefix]

        Returns
        -------
        fraud_score : float in [0.0, 1.0]
            Values >= 0.5 indicate fraudulent transaction.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")
        if len(features) != _EXPECTED_FEATURE_COUNT:
            raise ValueError(
                f"predict() expects exactly {_EXPECTED_FEATURE_COUNT} features, "
                f"got {len(features)}. Required order: "
                "[hour, day, month, year, merchant_category, amount, user_age, state_code, zip_prefix]"
            )
        arr    = np.array([features], dtype=np.float32)
        scaled = self.scaler.transform(arr)
        score  = float(self.model.predict(scaled, verbose=0)[0][0])
        return score

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# ── Module-level singleton ─────────────────────────────────────────────────────
_loader_instance: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """
    Returns the singleton ModelLoader instance.
    Thread-safe for reads (Python GIL); load() called only once at startup.
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ModelLoader()
    return _loader_instance

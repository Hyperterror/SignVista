"""
Fast single-sample inference for Keras models.

`model.predict()` is built for large batches and carries ~50-75 ms of
overhead per call, which dominates per-frame latency. A `tf.function` with a
fixed input signature runs the same graph in a few milliseconds and returns
identical outputs. Non-Keras objects (e.g. test doubles) fall back to
`.predict()`.
"""

import logging
from typing import Callable, Sequence

import numpy as np

logger = logging.getLogger(__name__)

Predictor = Callable[[np.ndarray], np.ndarray]


def make_predictor(model, feature_shape: Sequence[int]) -> Predictor:
    """Return fn(batch) -> probabilities for inputs shaped (N, *feature_shape)."""
    try:
        import tensorflow as tf

        if isinstance(model, tf.keras.Model):
            compiled = tf.function(
                lambda t: model(t, training=False),
                input_signature=[tf.TensorSpec([None, *feature_shape], tf.float32)],
                reduce_retracing=True,
            )

            def predict(batch: np.ndarray) -> np.ndarray:
                return compiled(tf.convert_to_tensor(batch, dtype=tf.float32)).numpy()

            return predict
    except Exception as e:  # pragma: no cover - TF missing or exotic model
        logger.warning(f"Falling back to model.predict(): {e}")

    def fallback(batch: np.ndarray) -> np.ndarray:
        return np.asarray(model.predict(batch, verbose=0))

    return fallback
